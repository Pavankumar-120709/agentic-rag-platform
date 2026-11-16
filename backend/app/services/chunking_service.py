"""
Multi-format Document Extraction and Token-Aware Chunking Service.
Supports PDF, TXT, and Markdown with boundary-sensitive recursive splitting.
"""
import io
import re
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from app.core.exceptions import DocumentIngestionError
from app.services.token_service import TokenService


class ExtractedPage:
    def __init__(self, page_number: Optional[int], text: str):
        self.page_number = page_number
        self.text = text


class RawChunk:
    def __init__(self, chunk_index: int, page_number: Optional[int], text: str, token_count: int, metadata: Dict[str, Any]):
        self.chunk_index = chunk_index
        self.page_number = page_number
        self.text = text
        self.token_count = token_count
        self.metadata = metadata


class ChunkingService:
    @classmethod
    def extract_text(cls, filename: str, content: bytes) -> List[ExtractedPage]:
        """Extracts text and page information from raw document bytes."""
        if not content or len(content.strip()) == 0:
            raise DocumentIngestionError(f"Document '{filename}' is empty.")

        ext = filename.lower().split(".")[-1] if "." in filename else ""

        if ext == "pdf":
            return cls._extract_pdf(filename, content)
        elif ext in ["txt", "text"]:
            return cls._extract_plain(content)
        elif ext in ["md", "markdown"]:
            return cls._extract_markdown(content)
        else:
            raise DocumentIngestionError(f"Unsupported file format '.{ext}'. Supported formats are: pdf, txt, md.")

    @classmethod
    def _extract_pdf(cls, filename: str, content: bytes) -> List[ExtractedPage]:
        try:
            reader = PdfReader(io.BytesIO(content))
            pages: List[ExtractedPage] = []
            total_text = ""
            for idx, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                total_text += page_text.strip()
                pages.append(ExtractedPage(page_number=idx + 1, text=page_text))

            if not total_text.strip():
                raise DocumentIngestionError(f"PDF document '{filename}' contains no extractable text.")
            return pages
        except Exception as e:
            if isinstance(e, DocumentIngestionError):
                raise
            raise DocumentIngestionError(f"Malformed or corrupt PDF file '{filename}': {str(e)}")

    @classmethod
    def _extract_plain(cls, content: bytes) -> List[ExtractedPage]:
        try:
            text = content.decode("utf-8")
        except UnicodeDecodeError:
            try:
                text = content.decode("latin-1")
            except Exception as e:
                raise DocumentIngestionError(f"Failed to decode text file: {str(e)}")
        if not text.strip():
            raise DocumentIngestionError("Text document contains no extractable text.")
        return [ExtractedPage(page_number=1, text=text)]

    @classmethod
    def _extract_markdown(cls, content: bytes) -> List[ExtractedPage]:
        return cls._extract_plain(content)

    @classmethod
    def chunk_document(
        cls,
        pages: List[ExtractedPage],
        chunk_size: int = 512,
        chunk_overlap: int = 64
    ) -> List[RawChunk]:
        """
        Token-aware boundary-sensitive chunking across pages.
        Preserves page numbering and structural breaks (newlines, headers).
        """
        raw_chunks: List[RawChunk] = []
        chunk_index = 0

        for page in pages:
            page_text = page.text.strip()
            if not page_text:
                continue

            # Split text by structural boundaries: double newlines, single newlines, then sentences
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", page_text) if p.strip()]
            
            current_chunk_words: List[str] = []
            current_tokens = 0

            for para in paragraphs:
                words = para.split()
                para_tokens = TokenService.count_tokens(para)

                if current_tokens + para_tokens <= chunk_size:
                    current_chunk_words.extend(words)
                    current_tokens += para_tokens
                else:
                    # Paragraph pushes chunk over limit. If current chunk already has words, flush it.
                    if current_chunk_words:
                        chunk_text = " ".join(current_chunk_words)
                        raw_chunks.append(RawChunk(
                            chunk_index=chunk_index,
                            page_number=page.page_number,
                            text=chunk_text,
                            token_count=TokenService.count_tokens(chunk_text),
                            metadata={"char_length": len(chunk_text)}
                        ))
                        chunk_index += 1
                        
                        # Retain overlap words
                        overlap_words = cls._get_overlap_words(current_chunk_words, chunk_overlap)
                        current_chunk_words = list(overlap_words)
                        current_tokens = TokenService.count_tokens(" ".join(current_chunk_words))

                    # If the paragraph itself is larger than chunk_size, split by sentences
                    if para_tokens > chunk_size:
                        sentences = re.split(r"(?<=[.!?])\s+", para)
                        for sent in sentences:
                            sent_words = sent.split()
                            sent_tokens = TokenService.count_tokens(sent)
                            if current_tokens + sent_tokens <= chunk_size:
                                current_chunk_words.extend(sent_words)
                                current_tokens += sent_tokens
                            else:
                                if current_chunk_words:
                                    chunk_text = " ".join(current_chunk_words)
                                    raw_chunks.append(RawChunk(
                                        chunk_index=chunk_index,
                                        page_number=page.page_number,
                                        text=chunk_text,
                                        token_count=TokenService.count_tokens(chunk_text),
                                        metadata={"char_length": len(chunk_text)}
                                    ))
                                    chunk_index += 1
                                    overlap_words = cls._get_overlap_words(current_chunk_words, chunk_overlap)
                                    current_chunk_words = list(overlap_words)
                                    current_tokens = TokenService.count_tokens(" ".join(current_chunk_words))
                                current_chunk_words.extend(sent_words)
                                current_tokens += sent_tokens
                    else:
                        current_chunk_words.extend(words)
                        current_tokens += para_tokens

            # Flush remaining words in the page
            if current_chunk_words:
                chunk_text = " ".join(current_chunk_words)
                raw_chunks.append(RawChunk(
                    chunk_index=chunk_index,
                    page_number=page.page_number,
                    text=chunk_text,
                    token_count=TokenService.count_tokens(chunk_text),
                    metadata={"char_length": len(chunk_text)}
                ))
                chunk_index += 1

        return raw_chunks

    @staticmethod
    def _get_overlap_words(words: List[str], target_overlap_tokens: int) -> List[str]:
        """Calculates overlap word slice based on target overlap tokens."""
        if not words or target_overlap_tokens <= 0:
            return []
        # Estimate ~0.75 words per token
        target_words = int(target_overlap_tokens * 0.75)
        return words[-target_words:] if len(words) > target_words else words

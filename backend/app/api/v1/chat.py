"""
FastAPI router for Conversational Agentic RAG, Chat Execution, and Conversation Management.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Conversation, Message, QueryExecution, RetrievalResult
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationRead,
    ConversationDetail,
    MessageRead,
    Citation
)
from app.workflow.graph import AgenticRAGGraph
from app.services.token_service import TokenService

router = APIRouter(tags=["Chat & Conversations"])


@router.post("/chat", response_model=ChatResponse)
def execute_chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Executes an end-to-end Agentic RAG query through the 15-node bounded workflow.
    Performs hybrid retrieval, RRF, cross-encoder reranking, query rewriting,
    grounded generation, citation verification, and faithfulness checking.
    """
    # 1. Resolve or create Conversation
    if request.conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == request.conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found.")
    else:
        title = request.query[:60] + "..." if len(request.query) > 60 else request.query
        conversation = Conversation(title=title)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # 2. Persist User Message
    user_msg = Message(
        conversation_id=conversation.id,
        role="user",
        content=request.query,
        citations_json=[],
        confidence_label="supported",
        token_count=TokenService.count_tokens(request.query)
    )
    db.add(user_msg)
    db.commit()

    # 3. Execute LangGraph Agentic Workflow
    state = AgenticRAGGraph.execute(
        db=db,
        query=request.query,
        conversation_id=conversation.id,
        retrieval_method=request.retrieval_method or "hybrid",
        max_rewrites=request.max_rewrites,
        context_token_budget=request.context_token_budget
    )

    # 4. Calculate cost
    cost_usd = TokenService.calculate_cost(state.prompt_tokens, state.completion_tokens)

    # 5. Persist Query Execution Record
    execution = QueryExecution(
        conversation_id=conversation.id,
        trace_id=state.trace_id,
        original_query=state.original_query,
        rewritten_queries=state.rewritten_queries,
        retrieval_method=state.retrieval_method,
        bm25_count=len(state.sparse_candidates),
        dense_count=len(state.dense_candidates),
        fused_count=len(state.fused_candidates),
        reranked_count=len(state.reranked_candidates),
        evidence_sufficient=state.evidence_sufficient,
        selected_context_tokens=state.selected_context_tokens,
        generation_attempts=state.generation_attempts,
        faithfulness_score=state.faithfulness_score,
        citation_valid=state.citation_valid,
        fallback_reason=state.fallback_reason,
        final_status=state.final_status,
        latency_ms=state.latency_ms,
        prompt_tokens=state.prompt_tokens,
        completion_tokens=state.completion_tokens,
        total_tokens=state.total_tokens,
        estimated_cost_usd=cost_usd
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    # 6. Persist Detailed Retrieval Results for Inspection
    all_candidates = state.reranked_candidates or state.fused_candidates
    for c in all_candidates:
        selected = any(sc.chunk_id == c.chunk_id for sc in state.selected_context)
        ret_res = RetrievalResult(
            execution_id=execution.id,
            chunk_id=c.chunk_id,
            document_id=c.document_id,
            filename=c.filename,
            chunk_index=c.chunk_index,
            page_number=c.page_number,
            sparse_rank=c.sparse_rank,
            dense_rank=c.dense_rank,
            rrf_score=c.rrf_score or 0.0,
            rerank_score=c.rerank_score,
            selected_for_context=selected,
            chunk_text=c.original_text
        )
        db.add(ret_res)

    # 7. Persist Assistant Message
    answer_resp = state.answer_response
    citations_data = [cite.model_dump() for cite in answer_resp.citations] if answer_resp else []

    assistant_msg = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer_resp.answer if answer_resp else "No answer generated.",
        citations_json=citations_data,
        confidence_label=answer_resp.confidence_label if answer_resp else "insufficient_evidence",
        token_count=TokenService.count_tokens(answer_resp.answer if answer_resp else ""),
        execution_id=execution.id
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    # Convert citations for response model
    typed_citations = [Citation(**c) for c in citations_data]

    message_read = MessageRead(
        id=assistant_msg.id,
        conversation_id=assistant_msg.conversation_id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        citations=typed_citations,
        confidence_label=assistant_msg.confidence_label,
        token_count=assistant_msg.token_count,
        execution_id=assistant_msg.execution_id,
        created_at=assistant_msg.created_at
    )

    return ChatResponse(
        conversation_id=conversation.id,
        message=message_read,
        answer_response=answer_resp,
        execution_id=execution.id,
        trace_id=state.trace_id,
        latency_ms=state.latency_ms,
        token_usage={
            "prompt_tokens": state.prompt_tokens,
            "completion_tokens": state.completion_tokens,
            "total_tokens": state.total_tokens,
            "estimated_cost_usd": cost_usd
        }
    )


@router.get("/conversations", response_model=List[ConversationRead])
def list_conversations(db: Session = Depends(get_db)):
    """Lists recent conversations."""
    return db.query(Conversation).order_by(Conversation.updated_at.desc()).all()


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Retrieves conversation thread and historical message exchanges."""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    
    # Map citations
    messages_read = []
    for m in conversation.messages:
        c_list = [Citation(**c) for c in (m.citations_json or [])]
        messages_read.append(MessageRead(
            id=m.id,
            conversation_id=m.conversation_id,
            role=m.role,
            content=m.content,
            citations=c_list,
            confidence_label=m.confidence_label,
            token_count=m.token_count,
            execution_id=m.execution_id,
            created_at=m.created_at
        ))

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=messages_read
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Deletes conversation and cascades messages."""
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    db.delete(conv)
    db.commit()
    return None

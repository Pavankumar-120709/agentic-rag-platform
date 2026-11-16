import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: string;
  badge?: string;
  className?: string;
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  badge,
  className,
}: MetricCardProps) {
  return (
    <div
      className={cn(
        "p-5 rounded-xl bg-[#0f172a] border border-[#1e293b] shadow-sm relative overflow-hidden transition hover:border-slate-700",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{title}</p>
        <div className="h-8 w-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <div className="mt-3 flex items-baseline gap-2">
        <p className="text-2xl font-bold text-white tracking-tight">{value}</p>
        {badge && (
          <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full border border-slate-700">
            {badge}
          </span>
        )}
      </div>
      {(subtitle || trend) && (
        <div className="mt-2 flex items-center justify-between text-xs">
          {subtitle && <span className="text-slate-400">{subtitle}</span>}
          {trend && <span className="text-emerald-400 font-medium">{trend}</span>}
        </div>
      )}
    </div>
  );
}

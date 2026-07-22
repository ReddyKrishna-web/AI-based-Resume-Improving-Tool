import type { CategoryScore } from "../types";

interface ScoreBreakdownProps {
  categories: CategoryScore[];
}

function getBarColor(score: number): string {
  if (score >= 80) return "bg-emerald-500";
  if (score >= 60) return "bg-blue-500";
  if (score >= 40) return "bg-amber-500";
  return "bg-red-500";
}

function getLabel(score: number): string {
  if (score >= 80) return "Strong";
  if (score >= 60) return "Good";
  if (score >= 40) return "Needs Work";
  return "Weak";
}

export default function ScoreBreakdown({ categories }: ScoreBreakdownProps) {
  return (
    <div className="card animate-slide-up">
      <h3 className="text-lg font-semibold text-slate-900 mb-6">
        Score Breakdown
      </h3>

      <div className="space-y-5">
        {categories.map((cat) => (
          <div key={cat.name}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-slate-700">
                  {cat.name}
                </span>
                <span className="text-xs text-slate-400">({(cat.weight * 100).toFixed(0)}% weight)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-sm font-semibold ${getBarColor(cat.score).replace("bg-", "text-")}`}>
                  {cat.score.toFixed(0)}/100
                </span>
                <span className={`badge ${cat.score >= 60 ? "badge-success" : cat.score >= 40 ? "badge-warning" : "badge-error"}`}>
                  {getLabel(cat.score)}
                </span>
              </div>
            </div>

            {/* Progress bar */}
            <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-1000 ease-out ${getBarColor(cat.score)}`}
                style={{ width: `${Math.max(cat.score, 2)}%` }}
              />
            </div>

            {/* Detail text */}
            <p className="mt-1.5 text-xs text-slate-500 leading-relaxed">
              {cat.details}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}

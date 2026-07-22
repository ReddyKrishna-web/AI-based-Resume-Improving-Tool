import type { ScoreResult } from "../types";

interface ScoreOverviewProps {
  score: ScoreResult;
}

const LEVEL_CONFIG = {
  excellent: { color: "text-emerald-600", bg: "bg-emerald-50", ring: "stroke-emerald-500", label: "Excellent" },
  good: { color: "text-blue-600", bg: "bg-blue-50", ring: "stroke-blue-500", label: "Good" },
  fair: { color: "text-amber-600", bg: "bg-amber-50", ring: "stroke-amber-500", label: "Fair" },
  poor: { color: "text-red-600", bg: "bg-red-50", ring: "stroke-red-500", label: "Poor" },
} as const;

export default function ScoreOverview({ score }: ScoreOverviewProps) {
  const config = LEVEL_CONFIG[score.level];
  const circumference = 2 * Math.PI * 45; // ≈ 282.7
  const offset = circumference - (score.total_score / 100) * circumference;

  return (
    <div className="card animate-slide-up">
      <div className="flex flex-col sm:flex-row items-center gap-8">
        {/* Score gauge */}
        <div className="relative flex-shrink-0">
          <svg width="120" height="120" viewBox="0 0 100 100" className="transform -rotate-90">
            {/* Background circle */}
            <circle
              cx="50" cy="50" r="45"
              fill="none"
              stroke="currentColor"
              strokeWidth="8"
              className="text-slate-100"
            />
            {/* Score arc */}
            <circle
              cx="50" cy="50" r="45"
              fill="none"
              strokeWidth="8"
              strokeLinecap="round"
              className={config.ring}
              strokeDasharray={circumference}
              strokeDashoffset={circumference}
              style={{
                strokeDashoffset: offset,
                transition: "stroke-dashoffset 1s ease-out",
              }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-3xl font-bold ${config.color}`}>
              {score.total_score}
            </span>
          </div>
        </div>

        {/* Score details */}
        <div className="flex-1 text-center sm:text-left">
          <h2 className="text-2xl font-bold text-slate-900 mb-1">
            {config.label}
          </h2>
          <p className="text-slate-500 text-sm mb-4">
            ATS Compatibility Score
          </p>
          <div className="flex flex-wrap gap-2 justify-center sm:justify-start">
            {score.categories.map((cat) => (
              <span
                key={cat.name}
                className={`badge ${
                  cat.score >= 70 ? "badge-success" : cat.score >= 40 ? "badge-warning" : "badge-error"
                }`}
                title={cat.details}
              >
                {cat.name}: {cat.score.toFixed(0)}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Level description */}
      <div className={`mt-6 p-4 rounded-xl ${config.bg}`}>
        <p className="text-sm font-medium">
          {score.level === "excellent" &&
            "Your resume is well-optimized for ATS. Minor tweaks can push it further."}
          {score.level === "good" &&
            "Solid resume with room for improvement. Focus on the lower-scoring categories below."}
          {score.level === "fair" &&
            "Your resume has some strengths but is missing key ATS optimization elements."}
          {score.level === "poor" &&
            "Significant improvements needed. The suggestions below can help raise your score."}
        </p>
      </div>
    </div>
  );
}

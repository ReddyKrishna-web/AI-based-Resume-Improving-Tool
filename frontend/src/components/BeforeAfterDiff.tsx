interface BeforeAfterDiffProps {
  original: string;
  suggestion: string;
}

export default function BeforeAfterDiff({ original, suggestion }: BeforeAfterDiffProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {/* Original */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-red-400" />
          Original
        </h4>
        <div className="p-3 bg-red-50 rounded-lg border border-red-100">
          <p className="text-sm text-slate-700 leading-relaxed">
            {original}
          </p>
        </div>
      </div>

      {/* Suggested */}
      <div className="space-y-2">
        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          Improved
        </h4>
        <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-100">
          <p className="text-sm text-slate-700 leading-relaxed">
            {suggestion}
          </p>
        </div>
      </div>
    </div>
  );
}

import { useState } from "react";
import type { Suggestion, SuggestionResult } from "../types";
import BeforeAfterDiff from "./BeforeAfterDiff";

interface SuggestionListProps {
  suggestions: SuggestionResult;
  warnings: string[];
  missingKeywords: string[];
}

export default function SuggestionList({
  suggestions,
  warnings,
  missingKeywords,
}: SuggestionListProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(0);

  if (!suggestions.generated && warnings.length === 0 && missingKeywords.length === 0) {
    return null;
  }

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="card border-amber-200 bg-amber-50/50">
          <h3 className="text-lg font-semibold text-slate-900 mb-3 flex items-center gap-2">
            <svg className="w-5 h-5 text-amber-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            Formatting Warnings
          </h3>
          <ul className="space-y-2">
            {warnings.map((w, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-600">
                <span className="text-amber-500 mt-0.5">•</span>
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Missing keywords */}
      {missingKeywords.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-slate-900 mb-3">
            Missing Keywords
          </h3>
          <div className="flex flex-wrap gap-2">
            {missingKeywords.map((kw, i) => (
              <span
                key={i}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-50 text-red-700 border border-red-200"
              >
                {kw}
              </span>
            ))}
          </div>
          <p className="mt-3 text-xs text-slate-500">
            Consider adding these keywords naturally to your skills and experience sections.
          </p>
        </div>
      )}

      {/* LLM Suggestions */}
      {suggestions.generated && suggestions.suggestions.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-slate-900 mb-1">
            Rewrite Suggestions
          </h3>
          <p className="text-sm text-slate-500 mb-6">
            AI-powered improvements for your weak points
            {suggestions.model_used && (
              <span className="text-xs text-slate-400 ml-2">
                (via {suggestions.model_used})
              </span>
            )}
          </p>

          <div className="space-y-3">
            {suggestions.suggestions.map((s, i) => (
              <SuggestionCard
                key={i}
                suggestion={s}
                index={i}
                isExpanded={expandedIndex === i}
                onToggle={() => setExpandedIndex(expandedIndex === i ? null : i)}
              />
            ))}
          </div>
        </div>
      )}

      {/* No suggestions generated */}
      {!suggestions.generated && (
        <div className="card bg-slate-50 text-center py-8">
          <svg className="w-10 h-10 text-slate-300 mx-auto mb-3" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
          </svg>
          <p className="text-sm text-slate-500">
            Suggestions unavailable. Set your <code className="bg-slate-200 px-1.5 rounded text-xs">OPENAI_API_KEY</code> to enable AI-powered rewrite suggestions.
          </p>
        </div>
      )}
    </div>
  );
}

function SuggestionCard({
  suggestion,
  index,
  isExpanded,
  onToggle,
}: {
  suggestion: Suggestion;
  index: number;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden transition-all duration-200 hover:border-slate-300">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-3 min-w-0">
          <span className="flex-shrink-0 w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 text-xs font-semibold flex items-center justify-center">
            {index + 1}
          </span>
          <div className="min-w-0">
            <span className="text-xs font-medium text-indigo-600 uppercase tracking-wide">
              {suggestion.section}
            </span>
            <p className="text-sm text-slate-600 truncate mt-0.5">
              {suggestion.original_text.slice(0, 80)}
              {suggestion.original_text.length > 80 ? "..." : ""}
            </p>
          </div>
        </div>
        <svg
          className={`w-5 h-5 text-slate-400 flex-shrink-0 transition-transform duration-200 ${
            isExpanded ? "rotate-180" : ""
          }`}
          fill="none"
          viewBox="0 0 24 24"
          strokeWidth={2}
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>

      {isExpanded && (
        <div className="border-t border-slate-100 p-4">
          <BeforeAfterDiff original={suggestion.original_text} suggestion={suggestion.suggestion} />
          <div className="mt-3 p-3 bg-indigo-50 rounded-lg">
            <h4 className="text-xs font-semibold text-indigo-700 uppercase tracking-wide mb-1">
              Why this matters
            </h4>
            <p className="text-sm text-slate-600">{suggestion.rationale}</p>
          </div>
        </div>
      )}
    </div>
  );
}

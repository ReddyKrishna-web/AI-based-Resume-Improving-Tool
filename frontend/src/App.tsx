import { useCallback, useState } from "react";
import type { AnalyzeResponse } from "./types";
import { analyzeResume } from "./api/client";
import Header from "./components/Header";
import UploadZone from "./components/UploadZone";
import ScoreOverview from "./components/ScoreOverview";
import ScoreBreakdown from "./components/ScoreBreakdown";
import SuggestionList from "./components/SuggestionList";

type AppState =
  | { phase: "upload" }
  | { phase: "loading" }
  | { phase: "results"; data: AnalyzeResponse }
  | { phase: "error"; message: string };

export default function App() {
  const [state, setState] = useState<AppState>({ phase: "upload" });

  const handleAnalyze = useCallback(async (file: File, jdText: string) => {
    setState({ phase: "loading" });
    try {
      const data = await analyzeResume(file, jdText);
      setState({ phase: "results", data });
    } catch (err) {
      setState({
        phase: "error",
        message: err instanceof Error ? err.message : "An unexpected error occurred.",
      });
    }
  }, []);

  const handleReset = useCallback(() => {
    setState({ phase: "upload" });
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {/* Upload phase */}
        {state.phase === "upload" && (
          <div className="space-y-8">
            <div className="text-center space-y-3">
              <h2 className="text-3xl font-bold text-slate-900 sm:text-4xl">
                Optimize Your Resume for ATS
              </h2>
              <p className="text-lg text-slate-500 max-w-xl mx-auto">
                Upload your resume to get a detailed ATS compatibility score,
                keyword gap analysis, and specific rewrite suggestions.
              </p>
            </div>

            <div className="max-w-lg mx-auto">
              <UploadZone onAnalyze={handleAnalyze} loading={false} />
            </div>

            {/* Features grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-12">
              {[
                {
                  icon: (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                  ),
                  title: "Parse",
                  desc: "Extract and structure your resume into sections",
                },
                {
                  icon: (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  ),
                  title: "Score",
                  desc: "Get a transparent, 0-100 ATS compatibility breakdown",
                },
                {
                  icon: (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5" />
                  ),
                  title: "Improve",
                  desc: "AI-powered rewrite suggestions for weak points",
                },
              ].map((feature, i) => (
                <div
                  key={i}
                  className="card text-center hover:border-indigo-200 hover:shadow-md transition-all duration-200"
                >
                  <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center mx-auto mb-3">
                    <svg className="w-5 h-5 text-indigo-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                      {feature.icon}
                    </svg>
                  </div>
                  <h3 className="font-semibold text-slate-900 mb-1">{feature.title}</h3>
                  <p className="text-xs text-slate-500">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Loading phase */}
        {state.phase === "loading" && (
          <div className="max-w-lg mx-auto">
            <UploadZone onAnalyze={handleAnalyze} loading={true} />
          </div>
        )}

        {/* Results phase */}
        {state.phase === "results" && (
          <div className="space-y-6">
            {/* Back button */}
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-700 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
              Analyze another resume
            </button>

            {/* Filename badge */}
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
              {state.data.filename}
              <span className="badge-info">{state.data.file_type?.toUpperCase()}</span>
            </div>

            {/* Score overview */}
            <ScoreOverview score={state.data.score} />

            {/* Score breakdown */}
            <ScoreBreakdown categories={state.data.score.categories} />

            {/* Suggestions */}
            <SuggestionList
              suggestions={state.data.suggestions}
              warnings={state.data.warnings}
              missingKeywords={state.data.match.missing_keywords}
            />
          </div>
        )}

        {/* Error phase */}
        {state.phase === "error" && (
          <div className="max-w-lg mx-auto text-center space-y-6">
            <div className="card border-red-200 bg-red-50">
              <div className="w-14 h-14 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
                <svg className="w-7 h-7 text-red-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-slate-900 mb-2">Analysis Failed</h3>
              <p className="text-sm text-slate-600 mb-6">{state.message}</p>
              <button onClick={handleReset} className="btn-secondary">
                Try Again
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-100 mt-16">
        <div className="max-w-3xl mx-auto px-4 py-6 text-center text-xs text-slate-400">
          Resume Optimizer — Built as a portfolio project. Scores are rule-based estimates, not guarantees.
        </div>
      </footer>
    </div>
  );
}

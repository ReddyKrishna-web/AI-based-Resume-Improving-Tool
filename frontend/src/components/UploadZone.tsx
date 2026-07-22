import { useCallback, useRef, useState } from "react";

interface UploadZoneProps {
  onAnalyze: (file: File, jdText: string) => void;
  loading: boolean;
}

export default function UploadZone({ onAnalyze, loading }: UploadZoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback((f: File): string | null => {
    const maxSize = 10 * 1024 * 1024; // 10 MB
    if (f.size > maxSize) return "File too large. Maximum size is 10 MB.";
    const ext = f.name.split(".").pop()?.toLowerCase();
    if (ext !== "pdf" && ext !== "docx") return "Only PDF and DOCX files are supported.";
    return null;
  }, []);

  const handleFile = useCallback(
    (f: File) => {
      setError(null);
      const err = validateFile(f);
      if (err) {
        setError(err);
        return;
      }
      setFile(f);
    },
    [validateFile]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) handleFile(droppedFile);
    },
    [handleFile]
  );

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else {
      setDragActive(false);
    }
  }, []);

  const handleSubmit = useCallback(() => {
    if (file) onAnalyze(file, jdText);
  }, [file, jdText, onAnalyze]);

  const removeFile = useCallback(() => {
    setFile(null);
    setError(null);
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Upload area */}
      <div
        className={`
          relative border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer
          transition-all duration-200
          ${
            dragActive
              ? "border-indigo-500 bg-indigo-50 scale-[1.02]"
              : file
              ? "border-emerald-300 bg-emerald-50"
              : "border-slate-200 bg-white hover:border-indigo-300 hover:bg-slate-50"
          }
        `}
        onDrop={handleDrop}
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onClick={() => !file && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />

        {file ? (
          <div className="space-y-3" onClick={(e) => e.stopPropagation()}>
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-emerald-100">
              <svg className="w-7 h-7 text-emerald-600" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <p className="font-medium text-slate-900">{file.name}</p>
              <p className="text-sm text-slate-500">
                {(file.size / 1024).toFixed(1)} KB
              </p>
            </div>
            <button
              onClick={removeFile}
              className="text-sm text-red-500 hover:text-red-700 transition-colors"
            >
              Remove file
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-100">
              <svg className="w-8 h-8 text-slate-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
            </div>
            <div>
              <p className="font-medium text-slate-700">
                Drop your resume here, or <span className="text-indigo-600">browse</span>
              </p>
              <p className="text-sm text-slate-400 mt-1">
                PDF or DOCX up to 10 MB
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="flex items-center gap-2 p-3 bg-red-50 rounded-xl border border-red-200 text-sm text-red-700">
          <svg className="w-5 h-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          {error}
        </div>
      )}

      {/* JD text area */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-slate-700">
          Target Job Description{" "}
          <span className="text-slate-400 font-normal">(optional — provides targeted suggestions)</span>
        </label>
        <textarea
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
          placeholder="Paste the job description here to get keyword-matched results..."
          rows={5}
          className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-white 
                     text-sm placeholder:text-slate-400
                     focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                     transition-all duration-200 resize-none"
        />
      </div>

      {/* Submit button */}
      <button
        onClick={handleSubmit}
        disabled={!file || loading}
        className="btn-primary w-full text-base py-4"
      >
        {loading ? (
          <span className="flex items-center gap-3">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Analyzing your resume...
          </span>
        ) : (
          <span className="flex items-center gap-2">
            Analyze Resume
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12h15m0 0l-6.75-6.75M19.5 12l-6.75 6.75" />
            </svg>
          </span>
        )}
      </button>
    </div>
  );
}

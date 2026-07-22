import type { AnalyzeResponse } from "../types";

const API_BASE = "/api";

export async function analyzeResume(
  file: File,
  jdText: string = ""
): Promise<AnalyzeResponse> {
  const formData = new FormData();
  formData.append("resume_file", file);
  formData.append("jd_text", jdText);

  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => null);
    const detail = errorData?.detail || response.statusText;
    throw new Error(detail);
  }

  return response.json();
}

export async function healthCheck(): Promise<{ status: string }> {
  const response = await fetch(`${API_BASE}/health`);
  return response.json();
}

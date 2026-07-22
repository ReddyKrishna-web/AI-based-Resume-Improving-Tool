/** TypeScript interfaces matching the backend AnalyzeResponse schema. */

export interface ContactInfo {
  email: string | null;
  phone: string | null;
  linkedin: string | null;
  location: string | null;
}

export interface EducationEntry {
  institution: string;
  degree: string;
  field: string;
  dates: string;
}

export interface BulletPoint {
  text: string;
  has_metric: boolean;
  has_strong_verb: boolean;
  suggestion: string | null;
}

export interface ExperienceEntry {
  company: string;
  title: string;
  dates: string;
  bullets: BulletPoint[];
}

export interface ProjectEntry {
  name: string;
  description: string;
  technologies: string[];
}

export interface StructuredResume {
  contact: ContactInfo;
  summary: string;
  education: EducationEntry[];
  experience: ExperienceEntry[];
  skills: string[];
  projects: ProjectEntry[];
  certifications: string[];
}

export interface FormattingIssue {
  issue_type: string;
  severity: string;
  message: string;
}

export interface MatchResult {
  jd_provided: boolean;
  matched_keywords: string[];
  missing_keywords: string[];
  keyword_match_pct: number;
  formatting_issues: FormattingIssue[];
}

export interface CategoryScore {
  name: string;
  score: number;
  weight: number;
  details: string;
}

export interface ScoreResult {
  total_score: number;
  level: "excellent" | "good" | "fair" | "poor";
  categories: CategoryScore[];
  max_possible: number;
}

export interface Suggestion {
  section: string;
  original_text: string;
  suggestion: string;
  rationale: string;
}

export interface SuggestionResult {
  suggestions: Suggestion[];
  generated: boolean;
  model_used: string | null;
}

export interface AnalyzeResponse {
  filename: string;
  file_type: "pdf" | "docx" | null;
  structured: StructuredResume;
  match: MatchResult;
  score: ScoreResult;
  suggestions: SuggestionResult;
  warnings: string[];
}

export type ScoreLevel = "excellent" | "good" | "fair" | "poor";

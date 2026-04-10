const API_BASE = 'http://localhost:8080';

export interface ScaffoldRequest {
  project_name: string;
  project_description: string;
  output_path: string;
  ides: string[];
}

export interface AnalyzeRequest {
  project_path: string;
  ides: string[];
  hint_path?: string;
}

export interface ApiResponse {
  files_written: string[];
  output_path: string;
}

export interface HintRequiredResponse {
  needs_hint: true;
}

export interface ErrorResponse {
  detail: string;
}

export interface CwdResponse {
  cwd: string;
}

export async function getCwd(): Promise<CwdResponse> {
  const response = await fetch(`${API_BASE}/api/cwd`);
  if (!response.ok) {
    throw new Error('Failed to get current directory');
  }
  return response.json();
}

export async function scaffoldProject(request: ScaffoldRequest): Promise<ApiResponse> {
  const response = await fetch(`${API_BASE}/api/scaffold`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.detail);
  }
  
  return response.json();
}

export async function analyzeProject(request: AnalyzeRequest): Promise<ApiResponse | HintRequiredResponse> {
  const response = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error: ErrorResponse = await response.json();
    throw new Error(error.detail);
  }
  
  return response.json();
}

export async function openFolder(path: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/open-folder?path=${encodeURIComponent(path)}`);
  if (!response.ok) {
    throw new Error('Failed to open folder');
  }
}
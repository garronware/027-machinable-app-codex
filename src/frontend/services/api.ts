import type {
  AnalysisResponse,
  RecalculationRequest,
  RecalculationResponse,
} from "../types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public body?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function parseResponse<T>(response: Response): Promise<T> {
  const body = await response.text();
  if (!response.ok) {
    let detail = body;
    try {
      const parsed = JSON.parse(body) as { detail?: string };
      detail = parsed.detail ?? body;
    } catch {
      // Preserve non-JSON provider and server errors.
    }
    throw new ApiError(
      detail || `Backend returned ${response.status}`,
      response.status,
      body,
    );
  }
  try {
    return JSON.parse(body) as T;
  } catch (error: unknown) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new ApiError(`Backend returned malformed JSON: ${detail}`, response.status, body);
  }
}

export async function analyzeDrawing(file: File): Promise<AnalysisResponse> {
  if (!file.name.toLowerCase().endsWith(".pdf")) {
    throw new ApiError("Choose a digitally generated PDF drawing.");
  }
  const formData = new FormData();
  formData.append("file", file);
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/analyze`, {
      method: "POST",
      body: formData,
    });
  } catch (error: unknown) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new ApiError(`Could not reach the analysis service: ${detail}`);
  }
  return parseResponse<AnalysisResponse>(response);
}

export async function recalculateStock(
  payload: RecalculationRequest,
): Promise<RecalculationResponse> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/recalculate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch (error: unknown) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new ApiError(`Could not reach the calculation service: ${detail}`);
  }
  return parseResponse<RecalculationResponse>(response);
}

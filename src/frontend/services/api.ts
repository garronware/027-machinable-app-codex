import type { FinalOutput } from "../types/api";

const BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL;

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

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export async function analyzeDrawing(
  uri: string,
  filename: string,
): Promise<FinalOutput> {
  if (!BASE_URL) {
    throw new ApiError(
      "EXPO_PUBLIC_API_BASE_URL is not set. Configure src/frontend/.env.",
    );
  }
  if (!filename.toLowerCase().endsWith(".pdf")) {
    throw new ApiError("Choose a PDF drawing.");
  }

  const formData = new FormData();
  const filePart = {
    uri,
    name: filename,
    type: "application/pdf",
  };
  formData.append("file", filePart as unknown as Blob);

  let response: Response;
  try {
    response = await fetch(`${BASE_URL}/analyze`, {
      method: "POST",
      body: formData,
    });
  } catch (error: unknown) {
    throw new ApiError(`Network request failed: ${describeError(error)}`);
  }

  const body = await response.text();
  if (!response.ok) {
    let detail = body;
    try {
      const parsed = JSON.parse(body) as { detail?: string };
      detail = parsed.detail ?? body;
    } catch {
      // Keep the raw body when it is not JSON.
    }
    throw new ApiError(detail || `Backend returned ${response.status}`, response.status, body);
  }

  try {
    return JSON.parse(body) as FinalOutput;
  } catch (error: unknown) {
    throw new ApiError(
      `Malformed JSON from backend: ${describeError(error)}`,
      response.status,
      body,
    );
  }
}


import type { Conversion, ConversionListItem, SectionKind } from "./types";

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(code: string, status: number) {
    super(code);
    this.name = "ApiError";
    this.code = code;
    this.status = status;
  }
}

function backendUrl(): string {
  const url = process.env.NEXT_PUBLIC_BACKEND_URL;
  if (!url) {
    throw new Error("NEXT_PUBLIC_BACKEND_URL is not set");
  }
  return url;
}

async function parseJsonOrThrow<T>(response: Response): Promise<T> {
  const text = await response.text();
  const data = text.length > 0 ? JSON.parse(text) : null;
  if (!response.ok) {
    const code = data && typeof data.error === "string" ? data.error : "unknown";
    throw new ApiError(code, response.status);
  }
  return data as T;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${backendUrl()}${path}`, {
      credentials: "include",
      ...init,
    });
  } catch {
    throw new ApiError("network", 0);
  }
  return parseJsonOrThrow<T>(response);
}

function jsonRequest<T>(path: string, method: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function listConversions(): Promise<ConversionListItem[]> {
  return request<ConversionListItem[]>("/conversions");
}

export function createConversion(file: File): Promise<Conversion> {
  const form = new FormData();
  form.append("file", file);
  form.append("website", "");
  return request<Conversion>("/conversions", { method: "POST", body: form });
}

export function getConversion(id: string): Promise<Conversion> {
  return request<Conversion>(`/conversions/${id}`);
}

export async function getSourceImageBlob(id: string): Promise<Blob> {
  let response: Response;
  try {
    response = await fetch(`${backendUrl()}/conversions/${id}/source_image`, {
      credentials: "include",
    });
  } catch {
    throw new ApiError("network", 0);
  }
  if (!response.ok) {
    const text = await response.text();
    const data = text.length > 0 ? JSON.parse(text) : null;
    const code = data && typeof data.error === "string" ? data.error : "unknown";
    throw new ApiError(code, response.status);
  }
  return response.blob();
}

export async function deleteConversion(id: string): Promise<void> {
  let response: Response;
  try {
    response = await fetch(`${backendUrl()}/conversions/${id}`, {
      method: "DELETE",
      credentials: "include",
    });
  } catch {
    throw new ApiError("network", 0);
  }
  if (!response.ok) {
    const text = await response.text();
    const data = text.length > 0 ? JSON.parse(text) : null;
    const code = data && typeof data.error === "string" ? data.error : "unknown";
    throw new ApiError(code, response.status);
  }
}

export function updateBandKind(
  conversionId: string,
  bandId: string,
  kind: SectionKind
): Promise<Conversion> {
  return jsonRequest<Conversion>(`/conversions/${conversionId}/bands/${bandId}`, "PATCH", {
    kind,
  });
}

export function mergeBand(
  conversionId: string,
  bandId: string,
  withBandId: string
): Promise<Conversion> {
  return jsonRequest<Conversion>(`/conversions/${conversionId}/bands/${bandId}/merge`, "POST", {
    with: withBandId,
  });
}

export function splitBand(conversionId: string, bandId: string, y: number): Promise<Conversion> {
  return jsonRequest<Conversion>(`/conversions/${conversionId}/bands/${bandId}/split`, "POST", {
    y,
  });
}

export function removeBand(conversionId: string, bandId: string): Promise<Conversion> {
  return request<Conversion>(`/conversions/${conversionId}/bands/${bandId}/remove`, {
    method: "POST",
  });
}

export function restoreBand(conversionId: string, bandId: string): Promise<Conversion> {
  return request<Conversion>(`/conversions/${conversionId}/bands/${bandId}/restore`, {
    method: "POST",
  });
}

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1"
).replace(/\/$/, "");

export interface ApiRequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  token?: string | null;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;
  readonly traceId: string | null;

  constructor(
    message: string,
    status: number,
    code = "HTTP_ERROR",
    details: unknown = null,
    traceId: string | null = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
    this.traceId = traceId;
  }
}

function buildUrl(path: string): string {
  if (/^https?:\/\//.test(path)) return path;
  return `${API_BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export async function apiFetch<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { body, token, headers: suppliedHeaders, ...rest } = options;
  const headers = new Headers(suppliedHeaders);
  headers.set("Accept", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let requestBody: BodyInit | undefined;
  if (body instanceof FormData) {
    requestBody = body;
  } else if (body !== undefined) {
    headers.set("Content-Type", "application/json");
    requestBody = JSON.stringify(body);
  }

  let response: Response;
  try {
    response = await fetch(buildUrl(path), {
      ...rest,
      headers,
      body: requestBody,
    });
  } catch {
    throw new ApiError(
      "Unable to reach the API. Check that the API service is running.",
      0,
      "NETWORK_ERROR",
    );
  }

  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try {
      payload = JSON.parse(text) as unknown;
    } catch {
      payload = text;
    }
  }

  if (!response.ok) {
    const body = payload as
      | {
          error?: { code?: string; message?: string; details?: unknown };
          traceId?: string;
        }
      | null;
    throw new ApiError(
      body?.error?.message ?? `Request failed with status ${response.status}`,
      response.status,
      body?.error?.code ?? "HTTP_ERROR",
      body?.error?.details ?? null,
      body?.traceId ?? null,
    );
  }

  return payload as T;
}

export const api = {
  get: <T>(path: string, token?: string | null) =>
    apiFetch<T>(path, { method: "GET", token }),
  post: <T>(path: string, body?: unknown, token?: string | null) =>
    apiFetch<T>(path, { method: "POST", body, token }),
  patch: <T>(path: string, body?: unknown, token?: string | null) =>
    apiFetch<T>(path, { method: "PATCH", body, token }),
  upload: <T>(path: string, body: FormData, token?: string | null) =>
    apiFetch<T>(path, { method: "POST", body, token }),
};

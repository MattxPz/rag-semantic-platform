import { useAuthStore } from "@/stores/auth-store";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

interface RequestOptions extends RequestInit {
  /** Explicit token override — only used during the login bootstrap flow. */
  token?: string;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token: tokenOverride, ...init } = options;
  const token = tokenOverride ?? useAuthStore.getState().token;

  const headers = new Headers(init.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_URL}${path}`, { ...init, headers });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const data = await response.json();
      if (typeof data.detail === "string") {
        detail = data.detail;
      } else if (Array.isArray(data.detail) && data.detail[0]?.msg) {
        // FastAPI/Pydantic validation errors come as an array of objects.
        detail = data.detail[0].msg;
      }
    } catch {
      // Response had no JSON body — keep the generic message.
    }
    throw new ApiError(detail, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const apiClient = {
  get: <T>(path: string, options?: { token?: string }) =>
    request<T>(path, { method: "GET", ...options }),

  postJson: <T>(path: string, body: unknown, options?: { token?: string }) =>
    request<T>(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      ...options,
    }),

  postForm: <T>(path: string, body: URLSearchParams) =>
    request<T>(path, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    }),

  postFile: <T>(path: string, formData: FormData) =>
    request<T>(path, {
      method: "POST",
      // No Content-Type here — the browser sets multipart/form-data with
      // the correct boundary automatically when the body is FormData.
      body: formData,
    }),
};

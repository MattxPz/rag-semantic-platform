import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient, ApiError } from "@/lib/api-client";

// Mock the auth store so the client doesn't depend on real state.
vi.mock("@/stores/auth-store", () => ({
  useAuthStore: {
    getState: () => ({ token: null }),
  },
}));

describe("apiClient", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns parsed JSON on a successful response", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ message: "success" }),
    } as Response);

    const result = await apiClient.get<{ message: string }>("/test");
    expect(result).toEqual({ message: "success" });
  });

  it("throws ApiError with the backend detail message on failure", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Something went wrong" }),
    } as Response);

    await expect(apiClient.get("/test")).rejects.toThrow(ApiError);
    await expect(apiClient.get("/test")).rejects.toThrow("Something went wrong");
  });

  it("extracts the first message from a FastAPI validation error array", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: [{ msg: "field required" }] }),
    } as Response);

    await expect(apiClient.get("/test")).rejects.toThrow("field required");
  });

  it("returns undefined for a 204 No Content response", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
    } as Response);

    const result = await apiClient.get("/test");
    expect(result).toBeUndefined();
  });
});
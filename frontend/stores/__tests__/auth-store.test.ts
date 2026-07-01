import { describe, it, expect, beforeEach } from "vitest";
import { useAuthStore } from "@/stores/auth-store";

describe("useAuthStore", () => {
  beforeEach(() => {
    // Reset to a clean state before each test.
    useAuthStore.setState({ token: null, user: null });
  });

  it("starts with no token or user", () => {
    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
  });

  it("stores token and user on setAuth", () => {
    const user = { id: "abc-123", email: "test@example.com" };
    useAuthStore.getState().setAuth("my-token", user);

    const state = useAuthStore.getState();
    expect(state.token).toBe("my-token");
    expect(state.user).toEqual(user);
  });

  it("clears token and user on clearAuth", () => {
    useAuthStore.getState().setAuth("my-token", { id: "abc-123", email: "test@example.com" });
    useAuthStore.getState().clearAuth();

    const state = useAuthStore.getState();
    expect(state.token).toBeNull();
    expect(state.user).toBeNull();
  });
});

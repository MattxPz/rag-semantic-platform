import { apiClient } from "@/lib/api-client";
import type { User } from "@/types";

interface LoginResponse {
  access_token: string;
  token_type: string;
}

export async function loginRequest(email: string, password: string): Promise<LoginResponse> {
  const body = new URLSearchParams();
  body.set("username", email); // the backend's OAuth2PasswordRequestForm expects "username"
  body.set("password", password);

  return apiClient.postForm<LoginResponse>("/auth/login", body);
}

export async function registerRequest(email: string, password: string): Promise<User> {
  return apiClient.postJson<User>("/auth/register", { email, password });
}

export async function fetchCurrentUser(token?: string): Promise<User> {
  return apiClient.get<User>("/auth/me", token ? { token } : undefined);
}
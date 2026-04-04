/**
 * Auth API functions: register, login, get current user.
 */

import { get, post } from "./client"
import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UserResponse,
} from "./types"

/** POST /auth/register */
export function register(data: RegisterRequest): Promise<UserResponse> {
  return post<UserResponse>("/auth/register", data)
}

/** POST /auth/login */
export function login(data: LoginRequest): Promise<TokenResponse> {
  return post<TokenResponse>("/auth/login", data)
}

/** GET /auth/me — requires valid JWT */
export function getMe(): Promise<UserResponse> {
  return get<UserResponse>("/auth/me")
}

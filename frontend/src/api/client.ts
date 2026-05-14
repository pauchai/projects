/**
 * Typed fetch wrapper with automatic JWT injection.
 *
 * All API calls go through this client. In dev mode, Vite proxies
 * /api/* to the backend. In production, nginx does the same.
 */

import { useAuthStore } from "@/stores/auth-store"
import type { ApiErrorResponse } from "./types"

const API_BASE = "/api"

/** Error thrown when an API call returns a non-OK status. */
export class ApiError extends Error {
  readonly status: number
  readonly detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = "ApiError"
    this.status = status
    this.detail = detail
  }
}

/**
 * Build full URL by prepending the API base path.
 *
 * @param path - Backend route path, e.g. "/auth/login"
 */
function buildUrl(path: string, params?: Record<string, string>): string {
  const url = new URL(`${API_BASE}${path}`, window.location.origin)
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined && value !== "") {
        url.searchParams.set(key, value)
      }
    }
  }
  return url.toString()
}

/**
 * Core fetch wrapper with JWT injection and error handling.
 *
 * @param options.token - Explicit JWT token. When provided, this token is
 *   used instead of reading from the auth store. This avoids race conditions
 *   when the token was just obtained but the store may not have persisted it
 *   yet (e.g. Telegram OAuth callback opening in a new tab).
 */
async function request<T>(
  path: string,
  options: RequestInit & { params?: Record<string, string>; token?: string } = {},
): Promise<T> {
  const { params, token: explicitToken, ...fetchOptions } = options

  const headers = new Headers(fetchOptions.headers)

  // Inject JWT token: prefer explicit token, fall back to auth store
  const token = explicitToken ?? useAuthStore.getState().token
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  // Default to JSON content type for requests with bodies
  if (fetchOptions.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }

  const response = await fetch(buildUrl(path, params), {
    ...fetchOptions,
    headers,
  })

  if (!response.ok) {
    // If 401, clear auth state (token expired or invalid)
    if (response.status === 401) {
      useAuthStore.getState().logout()
    }

    let detail = `HTTP ${response.status}`
    try {
      const body = (await response.json()) as ApiErrorResponse
      detail = body.detail || detail
    } catch {
      // response body wasn't JSON; use default detail
    }
    throw new ApiError(response.status, detail)
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

/**
 * Like request<T> but reads the response body as plain text.
 * Used for endpoints that return PlainTextResponse (e.g. file content).
 */
async function requestText(
  path: string,
  options: RequestInit & { params?: Record<string, string> } = {},
): Promise<string> {
  const { params, ...fetchOptions } = options

  const headers = new Headers(fetchOptions.headers)
  const token = useAuthStore.getState().token
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  const response = await fetch(buildUrl(path, params), { ...fetchOptions, headers })

  if (!response.ok) {
    if (response.status === 401) {
      useAuthStore.getState().logout()
    }
    let detail = `HTTP ${response.status}`
    try {
      const body = (await response.json()) as ApiErrorResponse
      detail = body.detail || detail
    } catch {
      // ignore
    }
    throw new ApiError(response.status, detail)
  }

  return response.text()
}

/** HTTP GET — response parsed as JSON */
export function get<T>(
  path: string,
  params?: Record<string, string>,
  token?: string,
): Promise<T> {
  return request<T>(path, { method: "GET", params, token })
}

/** HTTP GET — response read as plain text */
export function getText(path: string, params?: Record<string, string>): Promise<string> {
  return requestText(path, { method: "GET", params })
}

/** HTTP POST with JSON body */
export function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
}

/** HTTP PATCH with JSON body */
export function patch<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "PATCH",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
}

/** HTTP PUT with JSON body */
export function put<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "PUT",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
}

/** HTTP DELETE */
export function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" })
}

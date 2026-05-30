/**
 * Typed fetch wrapper with automatic JWT injection.
 */

import { useAuthStore } from "@/stores/auth-store"

const API_BASE = "/api"

export interface ApiErrorResponse {
  detail: string
}

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

async function request<T>(
  path: string,
  options: RequestInit & { params?: Record<string, string>; token?: string } = {},
): Promise<T> {
  const { params, token: explicitToken, ...fetchOptions } = options

  const headers = new Headers(fetchOptions.headers)

  const token = explicitToken ?? useAuthStore.getState().token
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  if (fetchOptions.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }

  const response = await fetch(buildUrl(path, params), {
    ...fetchOptions,
    headers,
  })

  if (!response.ok) {
    if (response.status === 401) {
      useAuthStore.getState().logout()
    }

    let detail = `HTTP ${response.status}`
    try {
      const body = (await response.json()) as ApiErrorResponse
      detail = body.detail || detail
    } catch {
      // not JSON
    }
    throw new ApiError(response.status, detail)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export function get<T>(
  path: string,
  params?: Record<string, string>,
  token?: string,
): Promise<T> {
  return request<T>(path, { method: "GET", params, token })
}

export function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
}

import { create } from "zustand"
import { persist } from "zustand/middleware"

export type UserStatus = "active" | "pending"

interface AuthState {
  token: string | null
  userId: string | null
  email: string | null
  displayName: string | null
  status: UserStatus | null
  isAuthenticated: boolean
  setAuth: (
    token: string,
    userId: string,
    email: string,
    displayName: string,
    status?: UserStatus,
  ) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userId: null,
      email: null,
      displayName: null,
      status: null,
      isAuthenticated: false,

      setAuth: (token, userId, email, displayName, status = "active") =>
        set({
          token,
          userId,
          email,
          displayName,
          status,
          isAuthenticated: true,
        }),

      logout: () =>
        set({
          token: null,
          userId: null,
          email: null,
          displayName: null,
          status: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: "schedule-auth-storage",
    },
  ),
)

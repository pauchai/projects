/**
 * TanStack Query hook for setting local password.
 */

import { useMutation } from "@tanstack/react-query"
import { setPassword } from "@/api/auth"

export function useSetPassword() {
  return useMutation({
    mutationFn: async (password: string) => {
      return setPassword({ password })
    },
  })
}
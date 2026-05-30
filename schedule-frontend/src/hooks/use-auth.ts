import { useMutation } from "@tanstack/react-query"
import { login } from "@/api/auth"
import { useAuthStore } from "@/stores/auth-store"

export function useLogin() {
  const { setAuth } = useAuthStore()
  return useMutation({
    mutationFn: login,
    onSuccess: (data) => {
      setAuth(
        data.access_token,
        data.user_id,
        data.email,
        data.display_name,
      )
    },
  })
}

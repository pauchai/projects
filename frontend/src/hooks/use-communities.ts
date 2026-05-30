import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "@/stores/auth-store"
import * as communityApi from "@/api/community"

export const COMMUNITIES_QUERY_KEY = ["communities"] as const

export function useCommunity(id: string | undefined) {
  return useQuery({
    queryKey: [...COMMUNITIES_QUERY_KEY, id],
    queryFn: () => communityApi.getCommunity(id!),
    enabled: !!id,
    staleTime: 30_000,
  })
}

export function useCommunities() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  return useQuery({
    queryKey: COMMUNITIES_QUERY_KEY,
    queryFn: communityApi.listCommunities,
    enabled: isAuthenticated,
    staleTime: 30_000,
  })
}

export function useCreateCommunity() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: communityApi.CreateCommunityRequest) =>
      communityApi.createCommunity(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: COMMUNITIES_QUERY_KEY })
    },
  })
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { useAuthStore } from "@/stores/auth-store"
import { useCommunityStore } from "@/stores/community-store"
import * as communityApi from "@/api/community"

export const COMMUNITIES_QUERY_KEY = ["communities"] as const

export function useCommunities() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const setSelectedCommunity = useCommunityStore((s) => s.setSelectedCommunity)
  const selectedCommunityId = useCommunityStore((s) => s.selectedCommunityId)

  const query = useQuery({
    queryKey: COMMUNITIES_QUERY_KEY,
    queryFn: communityApi.listCommunities,
    enabled: isAuthenticated,
    staleTime: 30_000,
  })

  const communities = query.data ?? []

  if (communities.length > 0 && !selectedCommunityId) {
    setSelectedCommunity(communities[0].community_id)
  }

  return query
}

export function useCreateCommunity() {
  const queryClient = useQueryClient()
  const setSelectedCommunity = useCommunityStore((s) => s.setSelectedCommunity)

  return useMutation({
    mutationFn: (data: communityApi.CreateCommunityRequest) =>
      communityApi.createCommunity(data),
    onSuccess: (community) => {
      queryClient.invalidateQueries({ queryKey: COMMUNITIES_QUERY_KEY })
      setSelectedCommunity(community.community_id)
    },
  })
}

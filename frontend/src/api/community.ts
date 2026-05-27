import { get, post } from "./client"

export interface CommunityResponse {
  community_id: string
  name: string
  description: string
  owner_id: string
  status: string
  member_count: number
  created_at: string
}

export interface CreateCommunityRequest {
  name: string
  description?: string
  avatar_url?: string | null
}

export function listCommunities(): Promise<CommunityResponse[]> {
  return get<CommunityResponse[]>("/communities")
}

export function createCommunity(data: CreateCommunityRequest): Promise<CommunityResponse> {
  return post<CommunityResponse>("/communities", data)
}

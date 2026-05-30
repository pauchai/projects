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

export interface MemberResponse {
  membership_id: string
  user_id: string
  role: string
  is_active: boolean
  joined_at: string
}

export interface CommunityDetailResponse extends CommunityResponse {
  avatar_url: string | null
  members: MemberResponse[]
}

export function listCommunities(): Promise<CommunityResponse[]> {
  return get<CommunityResponse[]>("/communities")
}

export function getCommunity(id: string): Promise<CommunityDetailResponse> {
  return get<CommunityDetailResponse>(`/communities/${id}`)
}

export function createCommunity(data: CreateCommunityRequest): Promise<CommunityResponse> {
  return post<CommunityResponse>("/communities", data)
}

import { apiClient } from "./client"
import type {
  GuaranteeRequestCreate,
  GuaranteeRequestResponse,
  ZeroCircleCreate,
  ZeroCircleResponse,
} from "./types"

// ---- Guarantee Requests ----

export const requestGuarantor = (body: GuaranteeRequestCreate) =>
  apiClient.post<GuaranteeRequestResponse>("/guarantorships/request", body)

export const acceptGuaranteeRequest = (requestId: string) =>
  apiClient.post<void>(`/guarantorships/${requestId}/accept`)

export const rejectGuaranteeRequest = (requestId: string) =>
  apiClient.post<void>(`/guarantorships/${requestId}/reject`)

export const getIncomingRequests = () =>
  apiClient.get<GuaranteeRequestResponse[]>("/guarantorships/incoming")

export const getOutgoingRequests = () =>
  apiClient.get<GuaranteeRequestResponse[]>("/guarantorships/outgoing")

// ---- Zero Circles ----

export const getZeroCircles = () =>
  apiClient.get<ZeroCircleResponse[]>("/zero-circles")

export const createZeroCircle = (body: ZeroCircleCreate) =>
  apiClient.post<ZeroCircleResponse>("/zero-circles", body)

export const joinZeroCircle = (circleId: string) =>
  apiClient.post<void>(`/zero-circles/${circleId}/join`)

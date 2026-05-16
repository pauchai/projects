import { get, post } from "./client"
import type {
  GuaranteeRequestCreate,
  GuaranteeRequestResponse,
  ZeroCircleCreate,
  ZeroCircleResponse,
} from "./types"

// ---- Guarantee Requests ----

export const requestGuarantor = (body: GuaranteeRequestCreate) =>
  post<GuaranteeRequestResponse>("/guarantorships/request", body)

export const acceptGuaranteeRequest = (requestId: string) =>
  post<void>(`/guarantorships/${requestId}/accept`)

export const rejectGuaranteeRequest = (requestId: string) =>
  post<void>(`/guarantorships/${requestId}/reject`)

export const getIncomingRequests = () =>
  get<GuaranteeRequestResponse[]>("/guarantorships/incoming")

export const getOutgoingRequests = () =>
  get<GuaranteeRequestResponse[]>("/guarantorships/outgoing")

// ---- Zero Circles ----

export const getZeroCircles = () =>
  get<ZeroCircleResponse[]>("/zero-circles")

export const createZeroCircle = (body: ZeroCircleCreate) =>
  post<ZeroCircleResponse>("/zero-circles", body)

export const joinZeroCircle = (circleId: string) =>
  post<void>(`/zero-circles/${circleId}/join`)

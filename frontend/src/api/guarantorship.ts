import { get, post } from "./client"
import type {
  ComplaintCreate,
  ComplaintResponse,
  DealCreate,
  DealResponse,
  DepositCreate,
  DepositResponse,
  GuaranteeRequestCreate,
  GuaranteeRequestResponse,
  GuarantorshipResponse,
  PlatformSettingsResponse,
  ZeroCircleCreate,
  ZeroCircleResponse,
} from "./types"

// ---- Guarantee Requests ----

export const requestGuarantor = (body: GuaranteeRequestCreate) =>
  post<GuaranteeRequestResponse>("/guarantorships/request", body)

export const acceptGuaranteeRequest = (requestId: string) =>
  post<GuarantorshipResponse>(`/guarantorships/${requestId}/accept`)

export const rejectGuaranteeRequest = (requestId: string) =>
  post<void>(`/guarantorships/${requestId}/reject`)

export const getIncomingRequests = () =>
  get<GuaranteeRequestResponse[]>("/guarantorships/incoming")

export const getOutgoingRequests = () =>
  get<GuaranteeRequestResponse[]>("/guarantorships/outgoing")

// ---- My Guarantorships ----

export const getMyGuarantorships = () =>
  get<GuarantorshipResponse[]>("/guarantorships/mine")

// ---- Deposits ----

export const getMyDeposits = () => get<DepositResponse[]>("/deposits")

export const createDeposit = (body: DepositCreate) =>
  post<DepositResponse>("/deposits", body)

// ---- Deals ----

export const getMyDeals = () => get<DealResponse[]>("/deals")

export const createDeal = (body: DealCreate) =>
  post<DealResponse>("/deals", body)

// ---- Complaints ----

export const getMyComplaints = () => get<ComplaintResponse[]>("/complaints")

export const fileComplaint = (body: ComplaintCreate) =>
  post<ComplaintResponse>("/complaints", body)

export const castVote = (complaintId: string, vote: string) =>
  post<ComplaintResponse>(`/complaints/${complaintId}/vote`, { vote })

export const escalateComplaint = (complaintId: string) =>
  post<ComplaintResponse>(`/complaints/${complaintId}/escalate`)

// ---- Platform Settings ----

export const getPlatformSettings = () =>
  get<PlatformSettingsResponse>("/platform-settings")

// ---- Zero Circles ----

export const getZeroCircles = () => get<ZeroCircleResponse[]>("/zero-circles")

export const createZeroCircle = (body: ZeroCircleCreate) =>
  post<ZeroCircleResponse>("/zero-circles", body)

export const joinZeroCircle = (circleId: string) =>
  post<void>(`/zero-circles/${circleId}/join`)

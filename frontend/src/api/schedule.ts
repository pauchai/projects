/**
 * Schedule API functions.
 *
 * Matches src/schedule/api/schemas.py
 */

import { get, post } from "./client"
import type {
  AddAvailabilitySlotRequest,
  AddAvailabilitySlotResponse,
  AppointmentResponse,
  AssignAppointmentRequest,
  ConsultationRequestResponse,
  CreateCuratorRequest,
  CuratorResponse,
  RespondToOfferRequest,
  RespondToOfferResponse,
  StartNegotiationResponse,
  SubmitConsultationRequestBody,
} from "./types"

/** POST /schedule/curators */
export function createCurator(data: CreateCuratorRequest): Promise<CuratorResponse> {
  return post<CuratorResponse>("/schedule/curators", data)
}

/** GET /schedule/curators */
export function listCurators(): Promise<CuratorResponse[]> {
  return get<CuratorResponse[]>("/schedule/curators")
}

/** POST /schedule/curators/:id/slots */
export function addAvailabilitySlot(
  curatorId: string,
  data: AddAvailabilitySlotRequest,
): Promise<AddAvailabilitySlotResponse> {
  return post<AddAvailabilitySlotResponse>(`/schedule/curators/${curatorId}/slots`, data)
}

/** POST /schedule/requests */
export function submitConsultationRequest(
  data: SubmitConsultationRequestBody,
): Promise<ConsultationRequestResponse> {
  return post<ConsultationRequestResponse>("/schedule/requests", data)
}

/** GET /schedule/requests */
export function listConsultationRequests(): Promise<ConsultationRequestResponse[]> {
  return get<ConsultationRequestResponse[]>("/schedule/requests")
}

/** POST /schedule/requests/:id/negotiate */
export function startNegotiation(requestId: string): Promise<StartNegotiationResponse> {
  return post<StartNegotiationResponse>(`/schedule/requests/${requestId}/negotiate`)
}

/** POST /schedule/offers/:id/respond */
export function respondToOffer(
  offerId: string,
  data: RespondToOfferRequest,
): Promise<RespondToOfferResponse> {
  return post<RespondToOfferResponse>(`/schedule/offers/${offerId}/respond`, data)
}

/** POST /schedule/requests/:id/assign */
export function assignAppointment(
  requestId: string,
  data: AssignAppointmentRequest,
): Promise<AppointmentResponse> {
  return post<AppointmentResponse>(`/schedule/requests/${requestId}/assign`, data)
}

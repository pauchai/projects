/** TypeScript types for the Schedule API. */

export interface ApiErrorResponse {
  detail: string
}

// Auth
export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: string
  email: string
  display_name: string
}

// Schedule

export interface AvailabilitySlotResponse {
  slot_id: string
  weekday: number
  start_time: string
  end_time: string
}

export interface CuratorResponse {
  curator_id: string
  name: string
  skills: string[]
  availability_slots: AvailabilitySlotResponse[]
}

export interface CreateCuratorRequest {
  name: string
  skills?: string[]
}

export interface AddAvailabilitySlotRequest {
  weekday: number
  start_time: string
  end_time: string
}

export interface AddAvailabilitySlotResponse {
  slot_id: string
}

export interface SubmitConsultationRequestBody {
  student_name: string
  request_text: string
}

export interface ConsultationRequestResponse {
  request_id: string
  student_name: string
  request_text: string
  status: "pending" | "negotiating" | "confirmed" | "cancelled"
  recommended_curator_ids: string[]
}

export interface StartNegotiationResponse {
  offer_ids: string[]
}

export interface RespondToOfferRequest {
  action: "accept" | "decline"
}

export interface RespondToOfferResponse {
  offer_id: string
  status: "accepted" | "declined"
}

export interface OfferResponse {
  offer_id: string
  request_id: string
  curator_id: string
  status: "pending" | "accepted" | "declined"
  student_name: string
  request_text: string
}

export interface AssignAppointmentRequest {
  scheduled_at: string
}

export interface AppointmentResponse {
  appointment_id: string
  request_id: string
  curator_id: string
  scheduled_at: string
  status: "scheduled" | "completed" | "cancelled"
}

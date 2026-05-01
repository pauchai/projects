/**
 * TanStack Query hooks for Schedule operations.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import * as scheduleApi from "@/api/schedule"
import type {
  AddAvailabilitySlotRequest,
  AssignAppointmentRequest,
  CreateCuratorRequest,
  RespondToOfferRequest,
  SubmitConsultationRequestBody,
} from "@/api/types"

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const scheduleKeys = {
  curators: ["schedule", "curators"] as const,
  requests: ["schedule", "requests"] as const,
}

// ---------------------------------------------------------------------------
// Curators
// ---------------------------------------------------------------------------

export function useCurators() {
  return useQuery({
    queryKey: scheduleKeys.curators,
    queryFn: scheduleApi.listCurators,
  })
}

export function useCreateCurator() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: CreateCuratorRequest) => scheduleApi.createCurator(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: scheduleKeys.curators })
    },
  })
}

export function useAddAvailabilitySlot(curatorId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: AddAvailabilitySlotRequest) =>
      scheduleApi.addAvailabilitySlot(curatorId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: scheduleKeys.curators })
    },
  })
}

// ---------------------------------------------------------------------------
// Consultation requests
// ---------------------------------------------------------------------------

export function useConsultationRequests() {
  return useQuery({
    queryKey: scheduleKeys.requests,
    queryFn: scheduleApi.listConsultationRequests,
  })
}

export function useSubmitConsultationRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: SubmitConsultationRequestBody) =>
      scheduleApi.submitConsultationRequest(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: scheduleKeys.requests })
    },
  })
}

// ---------------------------------------------------------------------------
// Negotiation
// ---------------------------------------------------------------------------

export function useStartNegotiation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (requestId: string) => scheduleApi.startNegotiation(requestId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: scheduleKeys.requests })
    },
  })
}

export function useRespondToOffer() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ offerId, data }: { offerId: string; data: RespondToOfferRequest }) =>
      scheduleApi.respondToOffer(offerId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: scheduleKeys.requests })
    },
  })
}

// ---------------------------------------------------------------------------
// Appointment
// ---------------------------------------------------------------------------

export function useAssignAppointment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      requestId,
      data,
    }: {
      requestId: string
      data: AssignAppointmentRequest
    }) => scheduleApi.assignAppointment(requestId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: scheduleKeys.requests })
    },
  })
}

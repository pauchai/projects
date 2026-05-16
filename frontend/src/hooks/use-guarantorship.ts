/**
 * TanStack Query hooks for the Guarantorship context.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  acceptGuaranteeRequest,
  createZeroCircle,
  getIncomingRequests,
  getOutgoingRequests,
  getZeroCircles,
  joinZeroCircle,
  rejectGuaranteeRequest,
  requestGuarantor,
} from "@/api/guarantorship"
import type { GuaranteeRequestCreate, ZeroCircleCreate } from "@/api/types"

export const guarantorshipKeys = {
  incoming: ["guarantorships", "incoming"] as const,
  outgoing: ["guarantorships", "outgoing"] as const,
  circles: ["zero-circles"] as const,
}

export function useIncomingRequests() {
  return useQuery({
    queryKey: guarantorshipKeys.incoming,
    queryFn: getIncomingRequests,
  })
}

export function useOutgoingRequests() {
  return useQuery({
    queryKey: guarantorshipKeys.outgoing,
    queryFn: getOutgoingRequests,
  })
}

export function useZeroCircles() {
  return useQuery({
    queryKey: guarantorshipKeys.circles,
    queryFn: getZeroCircles,
  })
}

export function useRequestGuarantor() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: GuaranteeRequestCreate) => requestGuarantor(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: guarantorshipKeys.outgoing })
    },
  })
}

export function useAcceptRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (requestId: string) => acceptGuaranteeRequest(requestId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: guarantorshipKeys.incoming })
    },
  })
}

export function useRejectRequest() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (requestId: string) => rejectGuaranteeRequest(requestId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: guarantorshipKeys.incoming })
    },
  })
}

export function useCreateZeroCircle() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: ZeroCircleCreate) => createZeroCircle(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: guarantorshipKeys.circles })
    },
  })
}

export function useJoinZeroCircle() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (circleId: string) => joinZeroCircle(circleId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: guarantorshipKeys.circles })
    },
  })
}

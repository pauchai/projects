/**
 * TanStack Query hooks for the Guarantorship context.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import {
  acceptGuaranteeRequest,
  castVote,
  createDeal,
  createDeposit,
  createZeroCircle,
  escalateComplaint,
  fileComplaint,
  getIncomingRequests,
  getMyComplaints,
  getMyDeals,
  getMyDeposits,
  getMyGuarantorships,
  getOutgoingRequests,
  getPlatformSettings,
  getZeroCircles,
  joinZeroCircle,
  rejectGuaranteeRequest,
  requestGuarantor,
} from "@/api/guarantorship"
import type {
  ComplaintCreate,
  DealCreate,
  DepositCreate,
  GuaranteeRequestCreate,
  ZeroCircleCreate,
} from "@/api/types"

export const guarantorshipKeys = {
  incoming: ["guarantorships", "incoming"] as const,
  outgoing: ["guarantorships", "outgoing"] as const,
  mine: ["guarantorships", "mine"] as const,
  circles: ["zero-circles"] as const,
  deposits: ["deposits"] as const,
  deals: ["deals"] as const,
  complaints: ["complaints"] as const,
  platformSettings: ["platform-settings"] as const,
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

export function useMyGuarantorships() {
  return useQuery({
    queryKey: guarantorshipKeys.mine,
    queryFn: getMyGuarantorships,
  })
}

export function useZeroCircles() {
  return useQuery({
    queryKey: guarantorshipKeys.circles,
    queryFn: getZeroCircles,
  })
}

export function useMyDeposits() {
  return useQuery({
    queryKey: guarantorshipKeys.deposits,
    queryFn: getMyDeposits,
  })
}

export function useMyDeals() {
  return useQuery({
    queryKey: guarantorshipKeys.deals,
    queryFn: getMyDeals,
  })
}

export function useMyComplaints() {
  return useQuery({
    queryKey: guarantorshipKeys.complaints,
    queryFn: getMyComplaints,
  })
}

export function usePlatformSettings() {
  return useQuery({
    queryKey: guarantorshipKeys.platformSettings,
    queryFn: getPlatformSettings,
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
      qc.invalidateQueries({ queryKey: guarantorshipKeys.mine })
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

export function useCreateDeposit() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: DepositCreate) => createDeposit(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: guarantorshipKeys.deposits })
    },
  })
}

export function useCreateDeal() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: DealCreate) => createDeal(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: guarantorshipKeys.deals })
    },
  })
}

export function useFileComplaint() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: ComplaintCreate) => fileComplaint(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: guarantorshipKeys.complaints })
    },
  })
}

export function useCastVote() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ complaintId, vote }: { complaintId: string; vote: string }) =>
      castVote(complaintId, vote),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: guarantorshipKeys.complaints })
    },
  })
}

export function useEscalateComplaint() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (complaintId: string) => escalateComplaint(complaintId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: guarantorshipKeys.complaints })
    },
  })
}

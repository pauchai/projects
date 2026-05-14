/**
 * TanStack Query hooks for project product operations.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import * as productsApi from "@/api/products"
import type { CreateProductRequest } from "@/api/types"

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const productKeys = {
  all: (projectId: string) => ["projects", projectId, "products"] as const,
}

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/** List all products for a project */
export function useProducts(projectId: string) {
  return useQuery({
    queryKey: productKeys.all(projectId),
    queryFn: () => productsApi.listProducts(projectId),
    enabled: !!projectId,
  })
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

/** Create a product for a project */
export function useCreateProduct(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: CreateProductRequest) =>
      productsApi.createProduct(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productKeys.all(projectId) })
    },
  })
}

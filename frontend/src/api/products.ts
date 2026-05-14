/**
 * Products API functions for a project's product catalog.
 */

import { get, post } from "./client"
import type { CreateProductRequest, ProductResponse } from "./types"

/** GET /projects/:id/products — list all products for a project */
export function listProducts(projectId: string): Promise<ProductResponse[]> {
  return get<ProductResponse[]>(`/projects/${projectId}/products`)
}

/** POST /projects/:id/products — create a new product */
export function createProduct(
  projectId: string,
  data: CreateProductRequest,
): Promise<ProductResponse> {
  return post<ProductResponse>(`/projects/${projectId}/products`, data)
}

/**
 * Global needs API: GET /needs — returns all open needs across all projects.
 */

import { get } from "./client"
import type { PublicNeedResponse } from "./types"

/** GET /needs — list all open needs (no auth required) */
export function getOpenNeeds(): Promise<PublicNeedResponse[]> {
  return get<PublicNeedResponse[]>("/needs")
}

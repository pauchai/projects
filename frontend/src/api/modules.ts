/**
 * API functions for Module & Topic endpoints.
 */

import { del, get, post } from "./client"
import type {
  AddTopicRequest,
  CreateModuleRequest,
  ModuleResponse,
} from "./types"

export const listModules = (): Promise<ModuleResponse[]> =>
  get<ModuleResponse[]>("/modules")

export const getModule = (moduleId: string): Promise<ModuleResponse> =>
  get<ModuleResponse>(`/modules/${moduleId}`)

export const createModule = (data: CreateModuleRequest): Promise<ModuleResponse> =>
  post<ModuleResponse>("/modules", data)

export const addTopic = (moduleId: string, data: AddTopicRequest): Promise<ModuleResponse> =>
  post<ModuleResponse>(`/modules/${moduleId}/topics`, data)

export const removeTopic = (moduleId: string, topicId: string): Promise<void> =>
  del<void>(`/modules/${moduleId}/topics/${topicId}`)

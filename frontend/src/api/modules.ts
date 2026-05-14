/**
 * API functions for Module, Topic, and Lesson endpoints.
 */

import { del, get, patch, post } from "./client"
import type {
  AddTopicRequest,
  CreateModuleRequest,
  LessonResponse,
  ModuleResponse,
  SyncResponse,
} from "./types"

// ---------------------------------------------------------------------------
// Modules
// ---------------------------------------------------------------------------

export const listModules = (): Promise<ModuleResponse[]> =>
  get<ModuleResponse[]>("/modules")

export const getModule = (moduleId: string): Promise<ModuleResponse> =>
  get<ModuleResponse>(`/modules/${moduleId}`)

export const createModule = (data: CreateModuleRequest): Promise<ModuleResponse> =>
  post<ModuleResponse>("/modules", data)

export const setRepoUrl = (
  moduleId: string,
  repoUrl: string | null,
): Promise<ModuleResponse> =>
  patch<ModuleResponse>(`/modules/${moduleId}/repo-url`, { repo_url: repoUrl })

// ---------------------------------------------------------------------------
// Topics
// ---------------------------------------------------------------------------

export const addTopic = (moduleId: string, data: AddTopicRequest): Promise<ModuleResponse> =>
  post<ModuleResponse>(`/modules/${moduleId}/topics`, data)

export const removeTopic = (moduleId: string, topicId: string): Promise<void> =>
  del<void>(`/modules/${moduleId}/topics/${topicId}`)

// ---------------------------------------------------------------------------
// Volume sync
// ---------------------------------------------------------------------------

export const syncModuleVolume = (moduleId: string): Promise<SyncResponse> =>
  post<SyncResponse>(`/modules/${moduleId}/sync`, {})

// ---------------------------------------------------------------------------
// Lessons
// ---------------------------------------------------------------------------

export const syncLessonsFromManifest = (moduleId: string): Promise<LessonResponse[]> =>
  post<LessonResponse[]>(`/modules/${moduleId}/sync-lessons`, {})

export const listLessons = (moduleId: string): Promise<LessonResponse[]> =>
  get<LessonResponse[]>(`/modules/${moduleId}/lessons`)

export const getLesson = (moduleId: string, lessonId: string): Promise<LessonResponse> =>
  get<LessonResponse>(`/modules/${moduleId}/lessons/${lessonId}`)

// ---------------------------------------------------------------------------
// File content (Markdown)
// ---------------------------------------------------------------------------

export const getLessonFile = (moduleId: string, filePath: string): Promise<string> =>
  get<string>(`/modules/${moduleId}/files/${filePath}`)

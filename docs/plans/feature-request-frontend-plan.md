# Feature Request System — Frontend Completion Plan

## Context

The Feature Request System backend is **100% implemented and tested** (638 tests passing).
The frontend has **0% implementation** — no pages, components, API client, or routing exist.

This plan covers building the complete frontend for feature requests, following existing project
conventions (React 19, TypeScript, TanStack Query, Zustand, ShadCN/UI, Tailwind CSS 4).

---

## Backend API Reference

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/features` | No | List all requests (optional `?status=` and `?author_id=` filters) |
| `POST` | `/features` | Yes | Submit new feature request |
| `GET` | `/features/{request_id}` | No | Get feature request details |
| `PUT` | `/admin/features/{request_id}/status` | Yes | Update status + admin notes |

### Data Model

```typescript
interface FeatureRequest {
  request_id: string
  author_id: string
  title: string          // 3-500 chars
  description: string    // max 10,000 chars
  status: "submitted" | "planned" | "in_progress" | "done" | "rejected"
  category: string | null
  priority: string | null
  admin_notes: string
  created_at: string     // ISO datetime
  updated_at: string     // ISO datetime
}
```

### Status Transitions

```
submitted --> planned --> in_progress --> done
    |             |            |
    v             v            v
 rejected      rejected     rejected
                               |
                               v
                            planned  (back to planned)
```

Terminal states: `done`, `rejected` — no outgoing transitions.

---

## Implementation Phases

### Phase 1: API Integration Layer

**Files to create/modify:**

1. **`frontend/src/api/client.ts`** — add `put()` helper (backend uses PUT for status update)
2. **`frontend/src/api/types.ts`** — add Feature Request types
3. **`frontend/src/api/features.ts`** — API functions for all 4 endpoints
4. **`frontend/src/hooks/use-features.ts`** — TanStack Query hooks

**Types to add:**
- `FeatureRequestResponse` — matches backend `FeatureRequestResponse` schema
- `CreateFeatureRequestRequest` — POST body
- `UpdateFeatureStatusRequest` — PUT body
- `ListFeaturesParams` — query parameters for GET /features

### Phase 2: Feature Request Card Component

**File:** `frontend/src/components/feature-card.tsx`

- Status badge with color-coded variants (like ProjectCard pattern)
- Title, truncated description, category/priority badges
- Date display (created_at)
- Click navigates to detail page

### Phase 3: Features List Page

**File:** `frontend/src/pages/features-list.tsx`

- List all feature requests
- Filter by status (All, Submitted, Planned, In Progress, Done, Rejected)
- Toggle "My Requests" (uses current user's ID as author_id filter)
- Loading/error/empty states
- Link to submit new request (authenticated users only)

### Phase 4: Submit Feature Request Page

**File:** `frontend/src/pages/submit-feature.tsx`

- Form with: title (required), description (required), category (optional), priority (optional)
- Client-side validation matching backend rules
- Character counters
- Submit button with loading state
- Redirect to detail page on success
- Protected route (requires authentication)

### Phase 5: Feature Detail Page

**File:** `frontend/src/pages/feature-detail.tsx`

- Full feature request details
- Status badge
- Admin notes section (if present)
- Timestamps (created, updated)
- Admin controls: status transition buttons + admin notes textarea
- Note: admin role check not enforced on backend yet (any authenticated user can update status)

### Phase 6: Routing & Navigation

**Files to modify:**

1. **`frontend/src/App.tsx`** — add routes:
   - `/features` — list page (public)
   - `/features/new` — submit page (protected)
   - `/features/:requestId` — detail page (public)

2. **`frontend/src/components/layout/header.tsx`** — add "Features" nav link

### Phase 7: Build Verification

- Run `npm run build` in frontend directory
- Verify no TypeScript errors
- Verify all routes load correctly

---

## Conventions

- File naming: `kebab-case.tsx`
- Components: `PascalCase` named exports
- Types: `PascalCase` with `Request`/`Response` suffixes
- Hooks: `use-<name>.ts`
- Query keys: factory object pattern (e.g., `featureKeys.all`, `featureKeys.detail(id)`)
- State: TanStack Query for server state, useState for local form state
- Styling: Tailwind CSS classes, ShadCN/UI components
- Error handling: `ApiError` class with `.detail` property
- IDs: `crypto.randomUUID()` for client-generated IDs

---

## Acceptance Criteria

- [ ] Users can browse all feature requests with status filtering
- [ ] Users can filter to see only their own requests
- [ ] Authenticated users can submit new feature requests
- [ ] Anyone can view feature request details
- [ ] Authenticated users can change request status and add admin notes
- [ ] Navigation includes "Features" link in header
- [ ] All pages have proper loading, error, and empty states
- [ ] Frontend builds without errors
- [ ] UI is consistent with existing project pages (ShadCN/UI, Tailwind)

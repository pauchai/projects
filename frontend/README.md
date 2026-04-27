# Frontend

React 19 + TypeScript SPA for the Project Collaboration Platform.

## Stack

| Tool | Purpose |
|------|---------|
| React 19 + Vite 8 | UI framework + dev server |
| TypeScript 5.9 (strict) | Type safety |
| Tailwind CSS 4 + shadcn/ui | Styling + component primitives |
| TanStack Query v5 | Server state + caching |
| Zustand v5 | Auth state (persisted to `localStorage`) |
| React Router v7 | Client-side routing |
| Playwright | E2E tests |

## Development

```bash
npm install
npm run dev      # Vite dev server → http://localhost:5173
npm run build    # Type-check + production build
npm run lint     # ESLint
```

The dev server proxies all `/api` requests to the backend at `localhost:8000`.

## E2E Tests

See the root [README — Running Tests](../README.md#running-tests) for the full
setup guide. Quick reference:

```bash
# Prerequisites: postgres-test container + backend on :8000 (see root README)

npm run test:e2e           # headless, list reporter
npm run test:e2e:ui        # interactive UI mode
npm run test:e2e:headed    # headed Chromium

# Single file / test
npx playwright test e2e/scenarios/task-flow.spec.ts
npx playwright test --grep "master creates a task"

# Open last HTML report
npx playwright show-report
```

### Test layout

```
e2e/
├── global-setup.ts          # DB reset (Alembic) + persona registration
├── fixtures.ts              # Per-role page + APIRequestContext fixtures
├── helpers/
│   └── seed.ts              # API helpers for seeding test data
└── scenarios/
    ├── access-control.spec.ts        # Route guards, role visibility
    ├── cohort-lifecycle.spec.ts      # Create / enrol / activate / cancel cohort
    ├── task-flow.spec.ts             # Create → activate → submit → review task
    ├── dashboard-validation.spec.ts  # Pending competency validation UI
    └── earnings.spec.ts             # /me/earnings page structure + auth guard
```

Generated files (git-ignored):

```
e2e/.auth/           # storageState JSON per persona
playwright-report/   # HTML test report
test-results/        # Artifacts from failed tests (screenshots, traces)
```

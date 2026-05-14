import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ThemeProvider } from "@/components/theme-provider"
import { Header } from "@/components/layout/header"
import { ProtectedRoute } from "@/components/layout/protected-route"

// Home
import { HomePage } from "@/pages/home"

// Projects — list / create
import { ProjectsListPage } from "@/pages/projects-list"
import { CreateProjectPage } from "@/pages/create-project"

// Project workspace
import { ProjectLayout } from "@/pages/project/layout"
import { ProjectOverviewPage } from "@/pages/project/overview"
import { ProjectProductsPage } from "@/pages/project/products"
import { ProjectTasksPage } from "@/pages/project/tasks"
import { ProjectPartnersPage } from "@/pages/project/partners"
import { ProjectDocsPage } from "@/pages/project/docs"
import { ProjectCoursesPage } from "@/pages/project/courses"
import { ProjectSettingsPage } from "@/pages/project/settings/index"
import { SettingsApplicationsPage } from "@/pages/project/settings/applications"

// Features
import { FeaturesListPage } from "@/pages/features-list"
import { SubmitFeaturePage } from "@/pages/submit-feature"
import { FeatureDetailPage } from "@/pages/feature-detail"

// Auth
import { ProfilePage } from "@/pages/profile"
import { SecuritySettingsPage } from "@/pages/settings/security"
import { SetPasswordPage } from "@/pages/settings/set-password"
import { LoginPage } from "@/pages/login"
import { RegisterPage } from "@/pages/register"
import { OAuthCallbackPage } from "@/pages/oauth-callback"
import { ActivationPage } from "@/pages/activate"
import { AdminInviteCodesPage } from "@/pages/admin-invite-codes"

// Cohorts
import { CohortsListPage } from "@/pages/cohorts-list"
import { CreateCohortPage } from "@/pages/create-cohort"
import { CohortDetailPage } from "@/pages/cohort-detail"
import { CohortDashboardPage } from "@/pages/cohort-dashboard"

// Modules
import { ModulesListPage } from "@/pages/modules-list"
import { CreateModulePage } from "@/pages/create-module"
import { ModuleDetailPage } from "@/pages/module-detail"

// Rewards / Earnings
import { RewardsPage } from "@/pages/rewards"
import { EarningsPage } from "@/pages/earnings"

// Schedule
import { CuratorsPage } from "@/pages/schedule/curators"
import { RequestsPage } from "@/pages/schedule/requests"
import { OffersPage } from "@/pages/schedule/offers"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
})

export default function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="vite-ui-theme">
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <div className="min-h-screen bg-background text-foreground">
            <Header />
            <main className="mx-auto max-w-5xl px-4 py-6">
              <Routes>
                {/* Home */}
                <Route path="/" element={<HomePage />} />

                {/* Admin */}
                <Route path="/admin" element={<AdminInviteCodesPage />} />

                {/* Auth */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/oauth/callback" element={<OAuthCallbackPage />} />
                <Route path="/activate" element={<ActivationPage />} />

                {/* Projects list / create */}
                <Route path="/projects" element={<ProjectsListPage />} />
                <Route
                  path="/projects/new"
                  element={
                    <ProtectedRoute>
                      <CreateProjectPage />
                    </ProtectedRoute>
                  }
                />

                {/* Project workspace — nested tabs */}
                <Route path="/projects/:projectId" element={<ProjectLayout />}>
                  {/* Redirect bare /projects/:id → overview */}
                  <Route index element={<Navigate to="overview" replace />} />
                  <Route path="overview" element={<ProjectOverviewPage />} />
                  <Route path="products" element={<ProjectProductsPage />} />
                  <Route path="tasks" element={<ProjectTasksPage />} />
                  <Route path="partners" element={<ProjectPartnersPage />} />
                  <Route path="docs" element={<ProjectDocsPage />} />
                  <Route path="courses" element={<ProjectCoursesPage />} />
                  <Route
                    path="settings"
                    element={
                      <ProtectedRoute>
                        <ProjectSettingsPage />
                      </ProtectedRoute>
                    }
                  />
                  <Route
                    path="settings/applications"
                    element={
                      <ProtectedRoute>
                        <SettingsApplicationsPage />
                      </ProtectedRoute>
                    }
                  />
                </Route>

                {/* Features */}
                <Route path="/features" element={<FeaturesListPage />} />
                <Route
                  path="/features/new"
                  element={
                    <ProtectedRoute>
                      <SubmitFeaturePage />
                    </ProtectedRoute>
                  }
                />
                <Route path="/features/:requestId" element={<FeatureDetailPage />} />

                {/* Cohorts */}
                <Route
                  path="/cohorts"
                  element={
                    <ProtectedRoute>
                      <CohortsListPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/cohorts/new"
                  element={
                    <ProtectedRoute>
                      <CreateCohortPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/cohorts/:cohortId"
                  element={
                    <ProtectedRoute>
                      <CohortDetailPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/cohorts/:cohortId/dashboard"
                  element={
                    <ProtectedRoute>
                      <CohortDashboardPage />
                    </ProtectedRoute>
                  }
                />

                {/* Modules */}
                <Route
                  path="/modules"
                  element={
                    <ProtectedRoute>
                      <ModulesListPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/modules/new"
                  element={
                    <ProtectedRoute>
                      <CreateModulePage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/modules/:moduleId"
                  element={
                    <ProtectedRoute>
                      <ModuleDetailPage />
                    </ProtectedRoute>
                  }
                />

                {/* Profile / account */}
                <Route
                  path="/profile"
                  element={
                    <ProtectedRoute>
                      <ProfilePage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/me/rewards"
                  element={
                    <ProtectedRoute>
                      <RewardsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/me/earnings"
                  element={
                    <ProtectedRoute>
                      <EarningsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/settings/security"
                  element={
                    <ProtectedRoute>
                      <SecuritySettingsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/settings/password"
                  element={
                    <ProtectedRoute>
                      <SetPasswordPage />
                    </ProtectedRoute>
                  }
                />

                {/* Schedule */}
                <Route
                  path="/schedule/curators"
                  element={
                    <ProtectedRoute>
                      <CuratorsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/schedule/requests"
                  element={
                    <ProtectedRoute>
                      <RequestsPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/schedule/offers"
                  element={
                    <ProtectedRoute>
                      <OffersPage />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  )
}

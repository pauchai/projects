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
import { ProjectSettingsPage } from "@/pages/project/settings/index"
import { SettingsApplicationsPage } from "@/pages/project/settings/applications"
import { ProjectFundPage } from "@/pages/project/fund"
import { ProjectFeaturesPage } from "@/pages/project/features"
import { ProjectModulesPage } from "@/pages/project/modules"
import { GuarantorshipPage } from "@/pages/guarantorship"

// Module workspace
import { ModuleLayout } from "@/pages/module/layout"
import { ModuleOverviewPage } from "@/pages/module/overview"
import { ModuleTopicsPage } from "@/pages/module/topics"
import { ModuleCohortsPage } from "@/pages/module/cohorts"
import { ModuleLessonsPage } from "@/pages/module/lessons"
import { ModuleSettingsPage } from "@/pages/module/settings"

// Cohort workspace
import { CohortLayout } from "@/pages/cohort/layout"
import { CohortOverviewPage } from "@/pages/cohort/overview"
import { CohortTasksPage } from "@/pages/cohort/tasks"
import { CohortProgressionPage } from "@/pages/cohort/progression"
import { CohortLeaderboardPage } from "@/pages/cohort/leaderboard"
import { CohortDashboardPage } from "@/pages/cohort/dashboard"

// Features
import { FeaturesListPage } from "@/pages/features-list"
import { SubmitFeaturePage } from "@/pages/submit-feature"
import { FeatureDetailPage } from "@/pages/feature-detail"

// Needs
import { NeedsListPage } from "@/pages/needs-list"

// Auth
import { ProfilePage } from "@/pages/profile"
import { SecuritySettingsPage } from "@/pages/settings/security"
import { SetPasswordPage } from "@/pages/settings/set-password"
import { LoginPage } from "@/pages/login"
import { RegisterPage } from "@/pages/register"
import { OAuthCallbackPage } from "@/pages/oauth-callback"
import { ActivationPage } from "@/pages/activate"
import { AdminInviteCodesPage } from "@/pages/admin-invite-codes"

// Create module / cohort (live inside project context)
import { CreateModulePage } from "@/pages/create-module"
import { CreateCohortPage } from "@/pages/create-cohort"

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
                <Route path="/needs" element={<NeedsListPage />} />
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
                  <Route index element={<Navigate to="overview" replace />} />
                  <Route path="overview" element={<ProjectOverviewPage />} />
                  <Route path="products" element={<ProjectProductsPage />} />
                  <Route path="fund" element={<ProjectFundPage />} />
                  <Route path="tasks" element={<ProjectTasksPage />} />
                  <Route path="partners" element={<ProjectPartnersPage />} />
                  <Route path="docs" element={<ProjectDocsPage />} />
                  <Route path="features" element={<ProjectFeaturesPage />} />
                  <Route
                    path="features/new"
                    element={
                      <ProtectedRoute>
                        <SubmitFeaturePage />
                      </ProtectedRoute>
                    }
                  />
                  <Route path="features/:requestId" element={<FeatureDetailPage />} />

                  {/* Modules tab */}
                  <Route path="modules" element={<ProjectModulesPage />} />
                  <Route
                    path="modules/new"
                    element={
                      <ProtectedRoute>
                        <CreateModulePage />
                      </ProtectedRoute>
                    }
                  />

                  {/* Module workspace (nested inside project) */}
                  <Route path="modules/:moduleId" element={<ModuleLayout />}>
                    <Route index element={<Navigate to="overview" replace />} />
                    <Route path="overview" element={<ModuleOverviewPage />} />
                    <Route path="topics" element={<ModuleTopicsPage />} />
                    <Route path="cohorts" element={<ModuleCohortsPage />} />
                    <Route path="lessons" element={<ModuleLessonsPage />} />
                    <Route
                      path="cohorts/new"
                      element={
                        <ProtectedRoute>
                          <CreateCohortPage />
                        </ProtectedRoute>
                      }
                    />

                    {/* Cohort workspace (nested inside module) */}
                    <Route path="cohorts/:cohortId" element={<CohortLayout />}>
                      <Route index element={<Navigate to="overview" replace />} />
                      <Route path="overview" element={<CohortOverviewPage />} />
                      <Route path="tasks" element={<CohortTasksPage />} />
                      <Route path="progression" element={<CohortProgressionPage />} />
                      <Route path="leaderboard" element={<CohortLeaderboardPage />} />
                      <Route
                        path="dashboard"
                        element={
                          <ProtectedRoute>
                            <CohortDashboardPage />
                          </ProtectedRoute>
                        }
                      />
                    </Route>

                    <Route
                      path="settings"
                      element={
                        <ProtectedRoute>
                          <ModuleSettingsPage />
                        </ProtectedRoute>
                      }
                    />
                  </Route>

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

                {/* Guarantorship */}
                <Route
                  path="/guarantorship"
                  element={
                    <ProtectedRoute>
                      <GuarantorshipPage />
                    </ProtectedRoute>
                  }
                />

                {/* Features (global) */}
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

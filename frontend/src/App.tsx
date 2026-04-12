import { BrowserRouter, Routes, Route } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { ThemeProvider } from "@/components/theme-provider"
import { Header } from "@/components/layout/header"
import { ProtectedRoute } from "@/components/layout/protected-route"
import { ProjectsListPage } from "@/pages/projects-list"
import { ProjectDetailPage } from "@/pages/project-detail"
import { CreateProjectPage } from "@/pages/create-project"
import { ManageApplicationsPage } from "@/pages/manage-applications"
import { FeaturesListPage } from "@/pages/features-list"
import { SubmitFeaturePage } from "@/pages/submit-feature"
import { FeatureDetailPage } from "@/pages/feature-detail"
import { ProfilePage } from "@/pages/profile"
import { SecuritySettingsPage } from "@/pages/settings/security"
import { LoginPage } from "@/pages/login"
import { RegisterPage } from "@/pages/register"
import { OAuthCallbackPage } from "@/pages/oauth-callback"

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
              <Route path="/" element={<ProjectsListPage />} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/oauth/callback" element={<OAuthCallbackPage />} />
              <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
              <Route
                path="/projects/new"
                element={
                  <ProtectedRoute>
                    <CreateProjectPage />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/projects/:projectId/applications"
                element={
                  <ProtectedRoute>
                    <ManageApplicationsPage />
                  </ProtectedRoute>
                }
              />
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
              <Route
                path="/profile"
                element={
                  <ProtectedRoute>
                    <ProfilePage />
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
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
    </ThemeProvider>
  )
}

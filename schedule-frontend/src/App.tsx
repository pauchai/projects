import { BrowserRouter, Routes, Route, Navigate, NavLink } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { CuratorsPage } from "@/pages/schedule/curators"
import { RequestsPage } from "@/pages/schedule/requests"
import { OffersPage } from "@/pages/schedule/offers"

const queryClient = new QueryClient()

function Header() {
  return (
    <header className="border-b bg-card px-4 py-3">
      <div className="mx-auto flex max-w-5xl items-center gap-4">
        <span className="font-semibold text-foreground">Schedule</span>
        <nav className="flex items-center gap-4">
          <NavLink
            to="/schedule/curators"
            className={({ isActive }) =>
              `text-sm ${isActive ? "font-medium text-foreground" : "text-muted-foreground hover:text-foreground"}`
            }
          >
            Curators
          </NavLink>
          <NavLink
            to="/schedule/requests"
            className={({ isActive }) =>
              `text-sm ${isActive ? "font-medium text-foreground" : "text-muted-foreground hover:text-foreground"}`
            }
          >
            Requests
          </NavLink>
          <NavLink
            to="/schedule/offers"
            className={({ isActive }) =>
              `text-sm ${isActive ? "font-medium text-foreground" : "text-muted-foreground hover:text-foreground"}`
            }
          >
            Offers
          </NavLink>
        </nav>
      </div>
    </header>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-background">
          <Header />
          <main className="mx-auto max-w-5xl px-4 py-6">
            <Routes>
              <Route path="/schedule/curators" element={<CuratorsPage />} />
              <Route path="/schedule/requests" element={<RequestsPage />} />
              <Route path="/schedule/offers" element={<OffersPage />} />
              <Route path="*" element={<Navigate to="/schedule/curators" replace />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App

import type { ReactNode } from "react"
import { useLocation } from "react-router-dom"
import { Sidebar } from "./sidebar"
import { FeedbackButton } from "@/components/feedback-button"

interface SidebarLayoutProps {
  children: ReactNode
}

export function SidebarLayout({ children }: SidebarLayoutProps) {
  const location = useLocation()

  const isAuthPage =
    location.pathname === "/login" ||
    location.pathname === "/register" ||
    location.pathname === "/oauth/callback" ||
    location.pathname.startsWith("/activate")

  if (isAuthPage) {
    return <div className="min-h-screen bg-background text-foreground">{children}</div>
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-6">{children}</div>
      </main>
      <FeedbackButton />
    </div>
  )
}

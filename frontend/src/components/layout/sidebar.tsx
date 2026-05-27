import { useState } from "react"
import { Link, useNavigate, useLocation } from "react-router-dom"
import {
  CheckSquare,
  ClipboardList,
  Store,
  Lightbulb,
  Users,
  Wallet,
  Plus,
  ChevronDown,
  LogOut,
  User,
  Building2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ModeToggle } from "@/components/mode-toggle"
import { useAuthStore } from "@/stores/auth-store"
import { useCommunityStore } from "@/stores/community-store"
import { useCommunities, useCreateCommunity } from "@/hooks/use-communities"
import { useLogout } from "@/hooks/use-auth"

const NAV_ITEMS = [
  { label: "Projects", href: "/projects", icon: ClipboardList },
  { label: "Needs", href: "/needs", icon: CheckSquare },
  { label: "Marketplace", href: "/marketplace", icon: Store },
  { label: "Feature Requests", href: "/features", icon: Lightbulb },
]

const COMMUNITY_NAV_ITEMS = [
  { label: "Members", icon: Users },
  { label: "Fund", icon: Wallet },
]

export function Sidebar() {
  const { isAuthenticated, displayName } = useAuthStore()
  const { selectedCommunityId, setSelectedCommunity } = useCommunityStore()
  const { data: communities = [] } = useCommunities()
  const createCommunity = useCreateCommunity()
  const logout = useLogout()
  const navigate = useNavigate()
  const location = useLocation()
  const [isCommunityOpen, setIsCommunityOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [newName, setNewName] = useState("")

  const selectedCommunity = communities.find((c) => c.community_id === selectedCommunityId)

  const handleLogout = () => {
    logout()
    navigate("/")
  }

  const handleCreateCommunity = async () => {
    if (!newName.trim()) return
    try {
      await createCommunity.mutateAsync({ name: newName.trim() })
      setNewName("")
      setIsCreating(false)
    } catch {
      // error handled by react query
    }
  }

  const isAuthPage =
    location.pathname === "/login" ||
    location.pathname === "/register" ||
    location.pathname === "/oauth/callback" ||
    location.pathname.startsWith("/activate")

  if (isAuthPage) return null

  return (
    <aside className="flex h-full w-64 flex-col border-r border-border bg-sidebar text-sidebar-foreground">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4">
        <Building2 className="h-5 w-5" />
        <Link to="/" className="text-lg font-bold tracking-tight">
          CollabHub
        </Link>
      </div>

      {/* Community selector */}
      {isAuthenticated && (
        <div className="border-b border-sidebar-border">
          <button
            onClick={() => setIsCommunityOpen(!isCommunityOpen)}
            className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
          >
            <span className="truncate">
              {selectedCommunity ? selectedCommunity.name : "Select community"}
            </span>
            <ChevronDown
              className={`h-4 w-4 shrink-0 transition-transform ${isCommunityOpen ? "rotate-180" : ""}`}
            />
          </button>

          {isCommunityOpen && (
            <div className="border-t border-sidebar-border px-2 pb-2 pt-1">
              {communities.map((c) => (
                <button
                  key={c.community_id}
                  onClick={() => {
                    setSelectedCommunity(c.community_id)
                    setIsCommunityOpen(false)
                  }}
                  className={`w-full rounded-md px-3 py-2 text-left text-sm transition-colors ${
                    c.community_id === selectedCommunityId
                      ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                      : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                  }`}
                >
                  <div className="truncate">{c.name}</div>
                  <div className="text-xs text-muted-foreground">{c.member_count} members</div>
                </button>
              ))}

              {isCreating ? (
                <div className="mt-2 space-y-2 px-1">
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="Community name"
                    className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-sm outline-none focus:ring-1 focus:ring-ring"
                    autoFocus
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleCreateCommunity()
                      if (e.key === "Escape") {
                        setIsCreating(false)
                        setNewName("")
                      }
                    }}
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={handleCreateCommunity} disabled={!newName.trim()}>
                      Create
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setIsCreating(false)
                        setNewName("")
                      }}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <button
                  onClick={() => setIsCreating(true)}
                  className="mt-1 flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
                >
                  <Plus className="h-4 w-4" />
                  Create community
                </button>
              )}
            </div>
          )}
        </div>
      )}

      {/* Nav menu */}
      <nav className="flex-1 overflow-y-auto px-2 py-4">
        <div className="space-y-1">
          <p className="px-3 pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {selectedCommunity ? selectedCommunity.name : "Navigation"}
          </p>
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname.startsWith(item.href)
            return (
              <Link
                key={item.href}
                to={item.href}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                    : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {item.label}
              </Link>
            )
          })}
        </div>

        {selectedCommunity && (
          <div className="mt-6 space-y-1">
            <p className="px-3 pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Community
            </p>
            {COMMUNITY_NAV_ITEMS.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.label}
                  className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {item.label}
                </button>
              )
            })}
          </div>
        )}
      </nav>

      {/* Bottom section: user */}
      <div className="border-t border-sidebar-border p-3">
        {isAuthenticated ? (
          <div className="space-y-2">
            <Link
              to="/profile"
              className="flex items-center gap-3 rounded-md px-2 py-1.5 text-sm text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground transition-colors"
            >
              <User className="h-4 w-4 shrink-0" />
              <span className="truncate">{displayName ?? "Profile"}</span>
            </Link>
            <div className="flex items-center justify-between px-2">
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <LogOut className="h-4 w-4" />
                Log out
              </button>
              <ModeToggle />
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center gap-2">
              <Link to="/login">
                <Button variant="outline" size="sm">
                  Log in
                </Button>
              </Link>
              <Link to="/register">
                <Button size="sm">Sign up</Button>
              </Link>
            </div>
            <ModeToggle />
          </div>
        )}
      </div>
    </aside>
  )
}

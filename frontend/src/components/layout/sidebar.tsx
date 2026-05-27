import { Link, useNavigate, useLocation } from "react-router-dom"
import {
  Building2,
  Globe,
  LogOut,
  User,
  ClipboardList,
  CheckSquare,
  Store,
  Lightbulb,
  Users,
  Wallet,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ModeToggle } from "@/components/mode-toggle"
import { useAuthStore } from "@/stores/auth-store"
import { useLogout } from "@/hooks/use-auth"
import { useCommunities } from "@/hooks/use-communities"

const COMMUNITY_NAV = [
  { label: "Projects", href: "/projects", icon: ClipboardList },
  { label: "Needs", href: "/needs", icon: CheckSquare },
  { label: "Marketplace", href: "/marketplace", icon: Store },
  { label: "Feature Requests", href: "/features", icon: Lightbulb },
  { label: "Members", href: "#", icon: Users },
  { label: "Fund", href: "#", icon: Wallet },
]

function useCommunityIdFromPath(): string | null {
  const location = useLocation()
  const match = location.pathname.match(/^\/communities\/([^/]+)/)
  return match ? match[1] : null
}

export function Sidebar() {
  const { isAuthenticated, displayName } = useAuthStore()
  const logout = useLogout()
  const navigate = useNavigate()
  const location = useLocation()
  const communityId = useCommunityIdFromPath()
  const { data: communities = [] } = useCommunities()

  const community = communityId
    ? communities.find((c) => c.community_id === communityId)
    : null

  const handleLogout = () => {
    logout()
    navigate("/")
  }

  const isAuthPage =
    location.pathname === "/login" ||
    location.pathname === "/register" ||
    location.pathname === "/oauth/callback" ||
    location.pathname.startsWith("/activate")

  if (isAuthPage) return null

  const navLinkClass = (active: boolean) =>
    `flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors ${
      active
        ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
        : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
    }`

  return (
    <aside className="flex h-full w-64 flex-col border-r border-border bg-sidebar text-sidebar-foreground">
      {/* Logo */}
      <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4">
        <Building2 className="h-5 w-5" />
        <Link to="/" className="text-lg font-bold tracking-tight">
          CollabHub
        </Link>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-2 py-4">
        <Link
          to="/communities"
          className={navLinkClass(
            location.pathname === "/communities" ||
              location.pathname === "/communities/",
          )}
        >
          <Globe className="h-4 w-4 shrink-0" />
          Communities
        </Link>

        {/* Community menu */}
        {community && (
          <div className="mt-4 space-y-1">
            <p className="px-3 pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground truncate">
              {community.name}
            </p>
            {COMMUNITY_NAV.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.label}
                  to={item.href}
                  className={navLinkClass(
                    item.href !== "#" && location.pathname.startsWith(item.href),
                  )}
                >
                  <Icon className="h-4 w-4 shrink-0" />
                  {item.label}
                </Link>
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

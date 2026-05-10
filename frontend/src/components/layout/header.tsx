import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { ChevronDown, Menu, User, X } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { ModeToggle } from "@/components/mode-toggle"
import { useAuthStore } from "@/stores/auth-store"
import { useLogout } from "@/hooks/use-auth"

export function Header() {
  const { isAuthenticated, displayName } = useAuthStore()
  const logout = useLogout()
  const navigate = useNavigate()
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const handleLogout = () => {
    logout()
    setIsMobileMenuOpen(false)
    navigate("/")
  }

  const closeMenu = () => setIsMobileMenuOpen(false)

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-background">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        {/* Logo */}
        <Link
          to="/"
          onClick={closeMenu}
          className="text-xl font-bold tracking-tight text-foreground hover:opacity-80"
        >
          CollabHub
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-6 flex-1 ml-8">
          {/* Zone 1: Public content */}
          <Link
            to="/"
            className="text-sm font-medium text-foreground hover:text-foreground/70 transition-colors"
          >
            Projects
          </Link>

          {/* Zone 2: Lab dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger>
              <span className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer select-none">
                Lab
                <ChevronDown className="h-3.5 w-3.5" />
              </span>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start">
              <DropdownMenuItem>
                <Link to="/features" className="w-full">Features</Link>
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Link to="/modules" className="w-full">Modules</Link>
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Link to="/cohorts" className="w-full">Cohorts</Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

        </div>

        {/* Zone 3: Right side — auth */}
        <div className="hidden md:flex items-center gap-3">
          <ModeToggle />
          {isAuthenticated ? (
            <DropdownMenu>
              <DropdownMenuTrigger>
                <Button variant="ghost" size="sm" className="flex items-center gap-1.5">
                  <User className="h-4 w-4" />
                  <span className="text-sm font-medium">{displayName ?? "Profile"}</span>
                  <ChevronDown className="h-3.5 w-3.5" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>
                  <Link to="/projects/new" className="w-full">Create project</Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <Link to="/me/rewards" className="w-full">Rewards</Link>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Link to="/me/earnings" className="w-full">Earnings</Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <Link to="/profile" className="w-full">Profile</Link>
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Link to="/settings/security" className="w-full">Security</Link>
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <button onClick={handleLogout} className="w-full text-left">Log out</button>
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <div className="flex items-center gap-2">
              <Link to="/login">
                <Button variant="outline" size="sm">Log in</Button>
              </Link>
              <Link to="/register">
                <Button size="sm">Sign up</Button>
              </Link>
            </div>
          )}
        </div>

        {/* Mobile: mode toggle + burger */}
        <div className="flex md:hidden items-center gap-2">
          <ModeToggle />
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9 px-0"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          >
            {isMobileMenuOpen ? (
              <X className="h-5 w-5" />
            ) : (
              <Menu className="h-5 w-5" />
            )}
            <span className="sr-only">Toggle menu</span>
          </Button>
        </div>
      </div>

      {/* Mobile menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-border bg-background px-4 py-4 shadow-sm absolute w-full z-50">
          <nav className="flex flex-col gap-1">
            {/* Zone 1: Public */}
            <Link
              to="/"
              onClick={closeMenu}
              className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-muted transition-colors"
            >
              Projects
            </Link>

            {/* Zone 2: Lab */}
            <div className="mt-2">
              <p className="px-3 py-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                Lab
              </p>
              <Link
                to="/features"
                onClick={closeMenu}
                className="block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              >
                Features
              </Link>
              <Link
                to="/modules"
                onClick={closeMenu}
                className="block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              >
                Modules
              </Link>
              <Link
                to="/cohorts"
                onClick={closeMenu}
                className="block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              >
                Cohorts
              </Link>
            </div>

            {/* Zone 3: Auth */}
            {isAuthenticated ? (
              <div className="mt-2 border-t border-border pt-2">
                <p className="px-3 py-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                  {displayName ?? "Profile"}
                </p>
                <Link
                  to="/projects/new"
                  onClick={closeMenu}
                  className="block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                >
                  Create project
                </Link>
                <Link
                  to="/me/rewards"
                  onClick={closeMenu}
                  className="block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                >
                  Rewards
                </Link>
                <Link
                  to="/me/earnings"
                  onClick={closeMenu}
                  className="block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                >
                  Earnings
                </Link>
                <Link
                  to="/profile"
                  onClick={closeMenu}
                  className="block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                >
                  Profile
                </Link>
                <Link
                  to="/settings/security"
                  onClick={closeMenu}
                  className="block rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                >
                  Security
                </Link>
                <button
                  onClick={handleLogout}
                  className="w-full text-left rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
                >
                  Log out
                </button>
              </div>
            ) : (
              <div className="mt-2 border-t border-border pt-3 flex flex-col gap-2">
                <Link to="/login" onClick={closeMenu}>
                  <Button variant="outline" size="sm" className="w-full">Log in</Button>
                </Link>
                <Link to="/register" onClick={closeMenu}>
                  <Button size="sm" className="w-full">Sign up</Button>
                </Link>
              </div>
            )}
          </nav>
        </div>
      )}
    </header>
  )
}

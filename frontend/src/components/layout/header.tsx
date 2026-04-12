import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Menu, X } from "lucide-react"
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
        <Link to="/" onClick={closeMenu} className="text-xl font-bold tracking-tight text-foreground hover:opacity-80">
          CollabHub
        </Link>

        <div className="flex items-center gap-2 md:gap-4">
          <nav className="hidden md:flex items-center gap-4">
            <Link
              to="/"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Projects
            </Link>
            <Link
              to="/features"
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Features
            </Link>

            {isAuthenticated ? (
              <>
                <Link
                  to="/projects/new"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Create
                </Link>
                <Link
                  to="/profile"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  {displayName ?? "Profile"}
                </Link>
                <Link
                  to="/settings/security"
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Security
                </Link>
                <Button variant="outline" size="sm" onClick={handleLogout}>
                  Log out
                </Button>
              </>
            ) : (
              <>
                <Link to="/login">
                  <Button variant="outline" size="sm">Log in</Button>
                </Link>
                <Link to="/register">
                  <Button size="sm">Sign up</Button>
                </Link>
              </>
            )}
          </nav>
          
          <ModeToggle />
          
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden h-9 w-9 px-0"
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

      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-border bg-background px-4 py-4 space-y-4 shadow-sm absolute w-full z-50">
          <nav className="flex flex-col gap-4">
            <Link
              to="/"
              onClick={closeMenu}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Projects
            </Link>
            <Link
              to="/features"
              onClick={closeMenu}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Features
            </Link>

            {isAuthenticated ? (
              <>
                <Link
                  to="/projects/new"
                  onClick={closeMenu}
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Create
                </Link>
                <Link
                  to="/profile"
                  onClick={closeMenu}
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  {displayName ?? "Profile"}
                </Link>
                <Link
                  to="/settings/security"
                  onClick={closeMenu}
                  className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                >
                  Security
                </Link>
                <Button variant="outline" size="sm" className="w-full justify-start" onClick={handleLogout}>
                  Log out
                </Button>
              </>
            ) : (
              <div className="flex flex-col gap-2 pt-2 border-t border-border">
                <Link to="/login" onClick={closeMenu} className="w-full">
                  <Button variant="outline" size="sm" className="w-full">Log in</Button>
                </Link>
                <Link to="/register" onClick={closeMenu} className="w-full">
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


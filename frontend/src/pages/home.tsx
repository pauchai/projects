/**
 * Home page — minimal landing.
 */

import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/auth-store"

export function HomePage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  return (
    <div className="flex flex-col items-center justify-center py-24 text-center space-y-6">
      <h1 className="text-4xl font-bold tracking-tight">
        Build together. Share the upside.
      </h1>
      <p className="max-w-lg text-muted-foreground text-lg">
        Partnr is a collaborative workspace where teams form projects, ship
        products, and split rewards — transparently and on-chain.
      </p>
      <div className="flex gap-3">
        <Link to="/projects">
          <Button size="lg">Explore Projects</Button>
        </Link>
        {!isAuthenticated && (
          <Link to="/register">
            <Button variant="outline" size="lg">Join Partnr</Button>
          </Link>
        )}
      </div>
    </div>
  )
}

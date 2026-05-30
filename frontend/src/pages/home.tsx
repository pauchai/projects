/**
 * Home page — bilingual landing.
 */

import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"
import { useAuthStore } from "@/stores/auth-store"

export function HomePage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

  return (
    <div className="flex flex-col items-center justify-center py-24 text-center space-y-8">

      {/* Hero */}
      <div className="space-y-3">
        <h1 className="text-4xl font-bold tracking-tight">
          Build together. Share the upside.
        </h1>
        <p className="text-2xl font-semibold tracking-tight text-muted-foreground">
          Создавайте вместе. Делитесь результатом.
        </p>
      </div>

      {/* Description */}
      <div className="max-w-xl space-y-2">
        <p className="text-muted-foreground text-lg">
          CollabHub is a collaborative workspace where teams form projects, find
          contributors, and exchange value — backed by a mutual guarantee system.
        </p>
        <p className="text-muted-foreground">
          CollabHub — совместное пространство, где команды формируют проекты,
          находят участников и обмениваются ценностью под защитой системы
          взаимного поручительства.
        </p>
      </div>

      {/* CTA */}
      <div className="flex flex-wrap justify-center gap-3">
        <Link to="/projects">
          <Button size="lg">Explore Projects / Проекты</Button>
        </Link>
        <Link to="/marketplace">
          <Button size="lg" variant="secondary">Marketplace / Маркетплейс</Button>
        </Link>
        <Link to="/needs">
          <Button size="lg" variant="outline">Open Needs / Потребности</Button>
        </Link>
        {!isAuthenticated && (
          <Link to="/register">
            <Button variant="outline" size="lg">Join / Вступить</Button>
          </Link>
        )}
      </div>
    </div>
  )
}

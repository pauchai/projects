/**
 * Marketplace — /marketplace
 *
 * Public page listing all active products across the platform.
 * Each card links to the project it belongs to.
 */

import { Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { useMarketplaceProducts } from "@/hooks/use-marketplace"
import type { ProductType } from "@/api/types"

const PRODUCT_TYPE_LABEL: Record<ProductType, string> = {
  course: "Course",
  mentoring: "Mentoring",
  onboarding: "Onboarding",
  donation: "Donation",
  other: "Other",
}

const PRODUCT_TYPE_VARIANT: Record<
  ProductType,
  "default" | "secondary" | "outline" | "destructive"
> = {
  course: "default",
  mentoring: "secondary",
  onboarding: "outline",
  donation: "secondary",
  other: "outline",
}

export function MarketplacePage() {
  const { data: products, isLoading, isError } = useMarketplaceProducts()

  if (isLoading) {
    return <p className="text-muted-foreground">Loading marketplace…</p>
  }

  if (isError) {
    return <p className="text-destructive">Failed to load marketplace.</p>
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">
          Marketplace / Маркетплейс
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Discover courses, mentoring sessions, and other offerings from projects on CollabHub.
        </p>
        <p className="mt-0.5 text-sm text-muted-foreground">
          Откройте для себя курсы, менторинг и другие продукты от проектов на CollabHub.
        </p>
      </div>

      {/* Empty state */}
      {(!products || products.length === 0) && (
        <div className="flex flex-col items-center gap-4 py-16 text-center">
          <p className="text-muted-foreground">No products available yet.</p>
          <Link to="/projects">
            <Button variant="outline">Browse projects</Button>
          </Link>
        </div>
      )}

      {/* Product grid */}
      {products && products.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {products.map((product) => (
            <Card key={product.product_id} className="flex flex-col justify-between">
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-base leading-snug">
                    {product.title}
                  </CardTitle>
                  <Badge
                    variant={PRODUCT_TYPE_VARIANT[product.product_type]}
                    className="shrink-0 text-xs"
                  >
                    {PRODUCT_TYPE_LABEL[product.product_type]}
                  </Badge>
                </div>
                <Link
                  to={`/projects/${product.project_id}`}
                  className="mt-0.5 text-sm font-medium text-primary hover:underline"
                >
                  {product.project_title}
                </Link>
              </CardHeader>

              <CardContent className="flex flex-col gap-3">
                {product.description && (
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {product.description}
                  </p>
                )}

                <Link to={`/projects/${product.project_id}`}>
                  <Button size="sm" variant="outline" className="mt-1">
                    View Project
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

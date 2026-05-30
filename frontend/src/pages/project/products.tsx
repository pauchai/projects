/**
 * Project workspace — Products tab.
 *
 * Lists products for the project. Owners/admins can create new products.
 * Visibility: public (all visitors see the product catalog).
 *
 * ref_id semantics:
 *   course    → cohort_id  (entered manually until /projects/:id/cohorts exists)
 *   mentoring → user_id    (selected from project members)
 *   others    → no ref_id
 */

import { useState } from "react"
import { useParams } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuthStore } from "@/stores/auth-store"
import { useProject } from "@/hooks/use-projects"
import { useProducts, useCreateProduct } from "@/hooks/use-products"
import type { ProductResponse, ProductType, ProductVisibility } from "@/api/types"

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PRODUCT_TYPE_LABELS: Record<ProductType, string> = {
  course: "Course",
  mentoring: "Mentoring",
  onboarding: "Onboarding",
  donation: "Donation",
  other: "Other",
}

/** Types that require a ref_id linking to an external entity */
const TYPES_WITH_REF: Set<ProductType> = new Set(["course", "mentoring"])

const VISIBILITY_VARIANT: Record<
  ProductVisibility,
  "default" | "secondary" | "outline"
> = {
  public: "default",
  members_only: "secondary",
}

// ---------------------------------------------------------------------------
// ProductCard
// ---------------------------------------------------------------------------

function ProductCard({ product }: { product: ProductResponse }) {
  return (
    <Card>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0 flex-1 space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-sm font-medium">{product.title}</span>
              <Badge variant="outline" className="text-xs">
                {PRODUCT_TYPE_LABELS[product.product_type] ?? product.product_type}
              </Badge>
              <Badge
                variant={VISIBILITY_VARIANT[product.visibility]}
                className="text-xs"
              >
                {product.visibility === "public" ? "Public" : "Members only"}
              </Badge>
              {!product.is_active && (
                <Badge variant="secondary" className="text-xs">
                  Inactive
                </Badge>
              )}
            </div>
            {product.description && (
              <p className="text-sm text-muted-foreground">{product.description}</p>
            )}
            {product.ref_id && (
              <p className="text-xs text-muted-foreground">
                {product.product_type === "course" && (
                  <span>Cohort: <code className="font-mono">{product.ref_id}</code></span>
                )}
                {product.product_type === "mentoring" && (
                  <span>Mentor ID: <code className="font-mono">{product.ref_id}</code></span>
                )}
              </p>
            )}
          </div>
          <div className="shrink-0 text-right">
            {product.price !== null ? (
              <span className="text-sm font-semibold">${product.price.toFixed(2)}</span>
            ) : (
              <span className="text-sm text-muted-foreground">Free</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// CreateProductForm
// ---------------------------------------------------------------------------

function CreateProductForm({
  projectId,
  onClose,
}: {
  projectId: string
  onClose: () => void
}) {
  const { data: project } = useProject(projectId)
  const createMutation = useCreateProduct(projectId)

  const [title, setTitle] = useState("")
  const [productType, setProductType] = useState<ProductType>("course")
  const [description, setDescription] = useState("")
  const [price, setPrice] = useState("")
  const [visibility, setVisibility] = useState<ProductVisibility>("public")
  const [refId, setRefId] = useState("")

  const needsRef = TYPES_WITH_REF.has(productType)

  // Members available for mentoring ref_id
  const activeMembers = project?.memberships.filter((m) => m.is_active) ?? []

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(
      {
        product_id: crypto.randomUUID(),
        title: title.trim(),
        product_type: productType,
        description: description || undefined,
        price: price.trim() ? Number(price) : null,
        visibility,
        ref_id: needsRef ? refId.trim() || undefined : undefined,
      },
      { onSuccess: onClose },
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">New Product</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Title */}
          <div className="space-y-2">
            <Label htmlFor="productTitle">
              Title <span className="text-destructive">*</span>
            </Label>
            <Input
              id="productTitle"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Product name"
              required
            />
          </div>

          {/* Type */}
          <div className="space-y-2">
            <Label htmlFor="productType">Type</Label>
            <select
              id="productType"
              value={productType}
              onChange={(e) => {
                setProductType(e.target.value as ProductType)
                setRefId("") // reset ref when type changes
              }}
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              {(Object.keys(PRODUCT_TYPE_LABELS) as ProductType[]).map((t) => (
                <option key={t} value={t}>
                  {PRODUCT_TYPE_LABELS[t]}
                </option>
              ))}
            </select>
          </div>

          {/* ref_id — cohort for course, member for mentoring */}
          {productType === "course" && (
            <div className="space-y-2">
              <Label htmlFor="refId">
                Cohort ID <span className="text-destructive">*</span>
              </Label>
              <Input
                id="refId"
                value={refId}
                onChange={(e) => setRefId(e.target.value)}
                placeholder="Paste cohort ID"
                required
              />
              <p className="text-xs text-muted-foreground">
                Link this product to an existing cohort in the learning module.
              </p>
            </div>
          )}

          {productType === "mentoring" && (
            <div className="space-y-2">
              <Label htmlFor="mentorId">
                Mentor <span className="text-destructive">*</span>
              </Label>
              {activeMembers.length > 0 ? (
                <select
                  id="mentorId"
                  value={refId}
                  onChange={(e) => setRefId(e.target.value)}
                  required
                  className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
                >
                  <option value="">Select a member…</option>
                  {activeMembers.map((m) => (
                    <option key={m.user_id} value={m.user_id}>
                      {m.user_id} ({m.role})
                    </option>
                  ))}
                </select>
              ) : (
                <Input
                  id="mentorId"
                  value={refId}
                  onChange={(e) => setRefId(e.target.value)}
                  placeholder="Mentor user ID"
                  required
                />
              )}
              <p className="text-xs text-muted-foreground">
                The project member who provides this mentoring session.
              </p>
            </div>
          )}

          {/* Description */}
          <div className="space-y-2">
            <Label htmlFor="productDescription">Description (optional)</Label>
            <Input
              id="productDescription"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Short description"
            />
          </div>

          {/* Price — not shown for donation (free-form) */}
          {productType !== "donation" && (
            <div className="space-y-2">
              <Label htmlFor="productPrice">Price (optional, USD)</Label>
              <Input
                id="productPrice"
                type="number"
                min="0"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="Leave empty for free"
              />
            </div>
          )}

          {/* Visibility */}
          <div className="space-y-2">
            <Label htmlFor="productVisibility">Visibility</Label>
            <select
              id="productVisibility"
              value={visibility}
              onChange={(e) => setVisibility(e.target.value as ProductVisibility)}
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <option value="public">Public</option>
              <option value="members_only">Members only</option>
            </select>
          </div>

          <div className="flex gap-2">
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? "Creating..." : "Create Product"}
            </Button>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
          </div>

          {createMutation.isError && (
            <p className="text-sm text-destructive">
              {createMutation.error instanceof Error
                ? createMutation.error.message
                : "Failed to create product"}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  )
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export function ProjectProductsPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { data: project } = useProject(projectId ?? "")
  const { data: products, isLoading, isError, error } = useProducts(projectId ?? "")
  const userId = useAuthStore((s) => s.userId)
  const [showForm, setShowForm] = useState(false)

  const isManager =
    !!userId &&
    !!project &&
    (project.owner_id === userId ||
      project.memberships.some(
        (m) =>
          m.user_id === userId &&
          m.is_active &&
          (m.role === "owner" || m.role === "admin"),
      ))

  if (isLoading) {
    return <p className="text-muted-foreground">Loading products...</p>
  }

  if (isError) {
    return (
      <p className="text-destructive">
        Failed to load products:{" "}
        {error instanceof Error ? error.message : "Unknown error"}
      </p>
    )
  }

  const productList = products ?? []

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Products ({productList.length})</h2>
        {isManager && !showForm && (
          <Button size="sm" onClick={() => setShowForm(true)}>
            Add Product
          </Button>
        )}
      </div>

      {showForm && projectId && (
        <CreateProductForm projectId={projectId} onClose={() => setShowForm(false)} />
      )}

      {productList.length === 0 && !showForm ? (
        <p className="text-sm text-muted-foreground">No products yet.</p>
      ) : (
        <div className="space-y-3">
          {productList.map((product) => (
            <ProductCard key={product.product_id} product={product} />
          ))}
        </div>
      )}
    </div>
  )
}

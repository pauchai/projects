import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useActivateAccount } from "@/hooks/use-auth"
import { ApiError } from "@/api/client"

export function ActivationPage() {
  const navigate = useNavigate()
  const activateMutation = useActivateAccount()

  const [inviteCode, setInviteCode] = useState("")
  const [fieldError, setFieldError] = useState<string | null>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (inviteCode.trim().length === 0) {
      setFieldError("Invite code is required")
      return
    }

    setFieldError(null)

    activateMutation.mutate(
      { invite_code: inviteCode.trim() },
      {
        onSuccess: () => {
          navigate("/", { replace: true })
        },
      },
    )
  }

  const serverError =
    activateMutation.error instanceof ApiError
      ? activateMutation.error.detail
      : activateMutation.error
        ? "Activation failed. Please check your invite code and try again."
        : null

  return (
    <div className="flex justify-center pt-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Activate your account</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-6 text-sm text-muted-foreground">
            Your account was created via social login. To unlock full access, enter
            an invite code from an existing member.
          </p>

          {serverError && (
            <p className="mb-4 text-sm text-destructive">{serverError}</p>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="invite-code">Invite code</Label>
              <Input
                id="invite-code"
                type="text"
                placeholder="e.g. ABC12345"
                value={inviteCode}
                onChange={(e) => setInviteCode(e.target.value)}
                aria-invalid={!!fieldError}
                autoComplete="off"
              />
              {fieldError && (
                <p className="text-sm text-destructive">{fieldError}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={activateMutation.isPending}
            >
              {activateMutation.isPending ? "Activating..." : "Activate account"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

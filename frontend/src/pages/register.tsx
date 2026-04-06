import { useState } from "react"
import { Link, useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { useRegister, useGoogleOAuthAvailable, useGoogleLogin } from "@/hooks/use-auth"
import { ApiError } from "@/api/client"

interface FormErrors {
  email?: string
  password?: string
  confirmPassword?: string
  displayName?: string
}

function validate(
  email: string,
  password: string,
  confirmPassword: string,
  displayName: string,
): FormErrors {
  const errors: FormErrors = {}

  const trimmedEmail = email.trim()
  if (trimmedEmail.length === 0) {
    errors.email = "Email is required"
  } else if (!trimmedEmail.includes("@")) {
    errors.email = "Invalid email format"
  }

  if (password.length === 0) {
    errors.password = "Password is required"
  } else if (password.length < 6) {
    errors.password = "Password must be at least 6 characters"
  }

  if (confirmPassword !== password) {
    errors.confirmPassword = "Passwords do not match"
  }

  const trimmedName = displayName.trim()
  if (trimmedName.length === 0) {
    errors.displayName = "Display name is required"
  } else if (trimmedName.length > 100) {
    errors.displayName = "Display name cannot exceed 100 characters"
  }

  return errors
}

export function RegisterPage() {
  const navigate = useNavigate()
  const registerMutation = useRegister()
  const googleLoginMutation = useGoogleLogin()
  const { data: oauthAvailable } = useGoogleOAuthAvailable()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [displayName, setDisplayName] = useState("")
  const [fieldErrors, setFieldErrors] = useState<FormErrors>({})

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const errors = validate(email, password, confirmPassword, displayName)
    setFieldErrors(errors)

    if (Object.keys(errors).length > 0) {
      return
    }

    registerMutation.mutate(
      {
        email: email.trim(),
        password,
        display_name: displayName.trim(),
      },
      {
        onSuccess: () => {
          navigate("/")
        },
      },
    )
  }

  const serverError =
    registerMutation.error instanceof ApiError
      ? registerMutation.error.detail
      : registerMutation.error
        ? "Registration failed. Please try again."
        : googleLoginMutation.error
          ? googleLoginMutation.error.message
          : null

  const isAnyPending = registerMutation.isPending || googleLoginMutation.isPending
  const isGoogleAvailable = oauthAvailable?.available === true

  const handleGoogleSignUp = () => {
    googleLoginMutation.mutate(undefined, {
      onSuccess: () => {
        navigate("/")
      },
    })
  }

  return (
    <div className="flex justify-center pt-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create an account</CardTitle>
        </CardHeader>
        <CardContent>
          {serverError && (
            <p className="mb-4 text-sm text-destructive">{serverError}</p>
          )}

          {isGoogleAvailable && (
            <>
              <Button
                type="button"
                variant="outline"
                className="w-full"
                disabled={isAnyPending}
                onClick={handleGoogleSignUp}
              >
                {googleLoginMutation.isPending
                  ? "Signing up..."
                  : "Sign up with Google"}
              </Button>

              <div className="relative my-6">
                <Separator />
                <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-card px-2 text-xs text-muted-foreground">
                  or
                </span>
              </div>
            </>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="displayName">Display name</Label>
              <Input
                id="displayName"
                type="text"
                placeholder="Your name"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                aria-invalid={!!fieldErrors.displayName}
              />
              {fieldErrors.displayName && (
                <p className="text-sm text-destructive">{fieldErrors.displayName}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                aria-invalid={!!fieldErrors.email}
              />
              {fieldErrors.email && (
                <p className="text-sm text-destructive">{fieldErrors.email}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={!!fieldErrors.password}
              />
              {fieldErrors.password && (
                <p className="text-sm text-destructive">{fieldErrors.password}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Repeat your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                aria-invalid={!!fieldErrors.confirmPassword}
              />
              {fieldErrors.confirmPassword && (
                <p className="text-sm text-destructive">{fieldErrors.confirmPassword}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isAnyPending}
            >
              {registerMutation.isPending ? "Creating account..." : "Sign up"}
            </Button>

            <p className="text-center text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link to="/login" className="text-primary underline hover:no-underline">
                Log in
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

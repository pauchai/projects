import { useState } from "react"
import { Link, useNavigate, useLocation } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { useLogin, useGoogleOAuthAvailable, useGoogleLogin, useTelegramOAuthAvailable, useTelegramLogin } from "@/hooks/use-auth"
import { ApiError } from "@/api/client"

interface FormErrors {
  email?: string
  password?: string
}

function validate(email: string, password: string): FormErrors {
  const errors: FormErrors = {}

  if (email.trim().length === 0) {
    errors.email = "Email is required"
  }

  if (password.length === 0) {
    errors.password = "Password is required"
  }

  return errors
}

export function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const loginMutation = useLogin()
  const googleLoginMutation = useGoogleLogin()
  const telegramLoginMutation = useTelegramLogin()
  const { data: oauthAvailable } = useGoogleOAuthAvailable()
  const { data: telegramAvailable } = useTelegramOAuthAvailable()

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [fieldErrors, setFieldErrors] = useState<FormErrors>({})

  /** Where to redirect after successful login */
  const from = (location.state as { from?: { pathname: string } } | null)?.from?.pathname ?? "/"

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const errors = validate(email, password)
    setFieldErrors(errors)

    if (Object.keys(errors).length > 0) {
      return
    }

    loginMutation.mutate(
      { email: email.trim(), password },
      {
        onSuccess: () => {
          navigate(from, { replace: true })
        },
      },
    )
  }

  const serverError =
    loginMutation.error instanceof ApiError
      ? loginMutation.error.detail
      : loginMutation.error
        ? "Login failed. Please try again."
        : googleLoginMutation.error
          ? googleLoginMutation.error.message
          : telegramLoginMutation.error
            ? telegramLoginMutation.error.message
            : null

  const isAnyPending = loginMutation.isPending || googleLoginMutation.isPending || telegramLoginMutation.isPending
  const isGoogleAvailable = oauthAvailable?.available === true
  const isTelegramAvailable = telegramAvailable?.available === true
  const isAnyOAuthAvailable = isGoogleAvailable || isTelegramAvailable

  const handleGoogleLogin = () => {
    googleLoginMutation.mutate(undefined, {
      onSuccess: () => {
        navigate(from, { replace: true })
      },
    })
  }

  return (
    <div className="flex justify-center pt-12">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Log in</CardTitle>
        </CardHeader>
        <CardContent>
          {serverError && (
            <p className="mb-4 text-sm text-destructive">{serverError}</p>
          )}

          {isAnyOAuthAvailable && (
            <>
              {isGoogleAvailable && (
                <Button
                  type="button"
                  variant="outline"
                  className="w-full"
                  disabled={isAnyPending}
                  onClick={handleGoogleLogin}
                >
                  {googleLoginMutation.isPending
                    ? "Signing in..."
                    : "Sign in with Google"}
                </Button>
              )}

              {isTelegramAvailable && (
                <Button
                  type="button"
                  variant="outline"
                  className="mt-2 w-full"
                  disabled={isAnyPending}
                  onClick={() => telegramLoginMutation.mutate()}
                >
                  {telegramLoginMutation.isPending
                    ? "Opening Telegram..."
                    : "Sign in with Telegram"}
                </Button>
              )}

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
                placeholder="Your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                aria-invalid={!!fieldErrors.password}
              />
              {fieldErrors.password && (
                <p className="text-sm text-destructive">{fieldErrors.password}</p>
              )}
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isAnyPending}
            >
              {loginMutation.isPending ? "Logging in..." : "Log in"}
            </Button>

            <p className="text-center text-sm text-muted-foreground">
              Don&apos;t have an account?{" "}
              <Link to="/register" className="text-primary underline hover:no-underline">
                Sign up
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

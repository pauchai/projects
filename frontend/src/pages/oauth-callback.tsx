/**
 * OAuth callback landing page.
 *
 * Handles two flows:
 * 1. Google OAuth (popup): The parent window polls this popup's URL to extract
 *    the authorization code, then closes the popup. Shows a loading message.
 * 2. Telegram OAuth (redirect): The user arrives here via a direct link from
 *    the Telegram bot. This page extracts code + state from URL params,
 *    exchanges them for a JWT, and redirects to the home page.
 */

import { useEffect } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { useTelegramCallback } from "@/hooks/use-auth"

export function OAuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const telegramCallback = useTelegramCallback()

  const code = searchParams.get("code")
  const state = searchParams.get("state")

  useEffect(() => {
    // Check if this is a Telegram callback (state stored in sessionStorage)
    const storedTelegramState = sessionStorage.getItem("telegram_oauth_state")

    if (code && state && storedTelegramState && state === storedTelegramState) {
      // Telegram flow: exchange code + state for JWT
      telegramCallback.mutate(
        { code, state },
        {
          onSuccess: () => {
            navigate("/", { replace: true })
          },
          onError: () => {
            navigate("/login", { replace: true })
          },
        },
      )
    }
    // Google flow: parent window polls the popup URL — nothing to do here
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code, state])

  if (telegramCallback.isPending) {
    return (
      <div className="flex justify-center pt-24">
        <p className="text-muted-foreground">Completing Telegram sign-in...</p>
      </div>
    )
  }

  if (telegramCallback.isError) {
    return (
      <div className="flex justify-center pt-24">
        <p className="text-destructive">
          Sign-in failed. Please try again from the login page.
        </p>
      </div>
    )
  }

  return (
    <div className="flex justify-center pt-24">
      <p className="text-muted-foreground">Completing sign-in...</p>
    </div>
  )
}

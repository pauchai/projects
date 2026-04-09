/**
 * OAuth callback landing page.
 *
 * Handles three flows:
 * 1. Google OAuth (popup): The parent window polls this popup's URL to extract
 *    the authorization code, then closes the popup. Shows a loading message.
 * 2. Telegram OAuth login (redirect): The user arrives here via a direct link
 *    from the Telegram bot. This page extracts code + state from URL params,
 *    validates state against localStorage (shared across tabs, unlike
 *    sessionStorage), exchanges them for a JWT, and redirects to the home page.
 * 3. Telegram OAuth linking (redirect): Same as above, but the user was linking
 *    a Telegram account to an existing session. Detected by
 *    localStorage "telegram_oauth_flow" === "link". On success, redirects
 *    to /settings/security.
 */

import { useEffect, useState } from "react"
import { useNavigate, useSearchParams } from "react-router-dom"
import { useTelegramCallback } from "@/hooks/use-auth"
import { useLinkTelegramCallback } from "@/hooks/use-credentials"

export function OAuthCallbackPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const telegramLoginCallback = useTelegramCallback()
  const telegramLinkCallback = useLinkTelegramCallback()
  const [stateMissing, setStateMissing] = useState(false)

  const code = searchParams.get("code")
  const state = searchParams.get("state")

  useEffect(() => {
    // Use localStorage instead of sessionStorage because the Telegram bot
    // link opens in a new tab / Telegram's embedded browser, and
    // sessionStorage is NOT shared across tabs.
    const storedTelegramState = localStorage.getItem("telegram_oauth_state")
    const telegramFlow = localStorage.getItem("telegram_oauth_flow")

    if (code && state && storedTelegramState && state === storedTelegramState) {
      if (telegramFlow === "link") {
        // Telegram account linking flow
        telegramLinkCallback.mutate(
          { code, state },
          {
            onSuccess: () => {
              navigate("/settings/security", { replace: true })
            },
            onError: () => {
              navigate("/settings/security", { replace: true })
            },
          },
        )
      } else {
        // Telegram login flow
        telegramLoginCallback.mutate(
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
    } else if (code && state) {
      // code and state are present in URL but stored state is missing or
      // doesn't match.  This happens when the link opens in a different
      // browser (e.g. Telegram's in-app browser) rather than the one that
      // initiated the flow.
      setStateMissing(true)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [code, state])

  const isPending = telegramLoginCallback.isPending || telegramLinkCallback.isPending
  const isError = telegramLoginCallback.isError || telegramLinkCallback.isError
  const isLinking = localStorage.getItem("telegram_oauth_flow") === "link"

  if (stateMissing) {
    return (
      <div className="flex flex-col items-center gap-4 pt-24">
        <p className="text-destructive">
          Sign-in session not found. Please open this link in the same browser
          where you started the Telegram login.
        </p>
        <button
          className="text-primary underline"
          onClick={() => navigate("/login", { replace: true })}
        >
          Back to login
        </button>
      </div>
    )
  }

  if (isPending) {
    return (
      <div className="flex justify-center pt-24">
        <p className="text-muted-foreground">
          {isLinking
            ? "Linking Telegram account..."
            : "Completing Telegram sign-in..."}
        </p>
      </div>
    )
  }

  if (isError) {
    return (
      <div className="flex justify-center pt-24">
        <p className="text-destructive">
          {isLinking
            ? "Failed to link Telegram account. Redirecting back to settings..."
            : "Sign-in failed. Please try again from the login page."}
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

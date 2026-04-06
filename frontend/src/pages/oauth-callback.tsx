/**
 * OAuth callback landing page.
 *
 * Google redirects the popup to this page after the user grants consent.
 * The parent window polls this popup's URL to extract the authorization code,
 * then closes the popup. This page just shows a brief loading message.
 */
export function OAuthCallbackPage() {
  return (
    <div className="flex justify-center pt-24">
      <p className="text-muted-foreground">Completing sign-in...</p>
    </div>
  )
}

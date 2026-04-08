/**
 * Security Settings page — displays connected sign-in methods.
 *
 * Shows a list of credential cards (Email & Password, Google, Telegram)
 * for the currently authenticated user. Read-only for now; the architecture
 * supports adding/removing methods in a future iteration.
 */

import { Link } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { useUserCredentials } from "@/hooks/use-credentials"
import type { CredentialResponse } from "@/api/types"

/** Map provider identifiers to descriptive icons / labels for the UI. */
const PROVIDER_ICONS: Record<string, string> = {
  local: "\u{1F512}",
  google: "\u{1F310}",
  telegram: "\u{2708}\uFE0F",
}

function getProviderIcon(provider: string): string {
  return PROVIDER_ICONS[provider] ?? "\u{1F511}"
}

function CredentialCard({ credential }: { credential: CredentialResponse }) {
  return (
    <Card size="sm">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span className="text-lg">{getProviderIcon(credential.provider)}</span>
          <span>{credential.provider_display_name}</span>
          {!credential.is_removable && (
            <Badge variant="secondary" className="ml-auto text-xs">
              Primary
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Linked account: {credential.provider_user_id}
        </p>
      </CardContent>
    </Card>
  )
}

export function SecuritySettingsPage() {
  const { data, isLoading, isError, error } = useUserCredentials()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Security Settings</h1>
        <p className="text-sm text-muted-foreground">
          Manage your sign-in methods and account security.
        </p>
      </div>

      <Separator />

      <section>
        <h2 className="mb-4 text-lg font-semibold">Connected Sign-in Methods</h2>

        {isLoading && (
          <p className="text-sm text-muted-foreground">Loading credentials...</p>
        )}

        {isError && (
          <p className="text-sm text-destructive">
            Failed to load credentials: {error?.message ?? "Unknown error"}
          </p>
        )}

        {data && (
          <>
            <div className="mb-4 text-sm text-muted-foreground">
              Signed in as <span className="font-medium text-foreground">{data.user_display_name}</span>
              {" "}({data.user_email})
              {" "}&middot;{" "}
              {data.total_count} {data.total_count === 1 ? "method" : "methods"} connected
            </div>

            {data.credentials.length > 0 ? (
              <div className="grid gap-3">
                {data.credentials.map((credential) => (
                  <CredentialCard
                    key={credential.credential_id}
                    credential={credential}
                  />
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                No sign-in methods found. This shouldn't happen — please contact
                support.
              </p>
            )}
          </>
        )}
      </section>

      <Separator />

      <div className="text-sm text-muted-foreground">
        <Link
          to="/profile"
          className="text-primary underline-offset-4 hover:underline"
        >
          &larr; Back to Profile
        </Link>
      </div>
    </div>
  )
}

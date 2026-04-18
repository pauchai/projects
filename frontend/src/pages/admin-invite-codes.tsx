/**
 * Admin — Invite Codes management page (/admin)
 *
 * Allows the admin to:
 * - Enter the admin secret
 * - Generate a batch of invite codes
 * - View all existing invite codes with their status
 */

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"

const API_BASE = "/api"

interface InviteCode {
  code_id: string
  code: string
  uses_left: number
  max_uses: number
  is_active: boolean
  created_at: string
}

async function apiFetch<T>(
  path: string,
  secret: string,
  options: RequestInit = {},
): Promise<{ data: T | null; error: string | null }> {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Secret": secret,
        ...(options.headers ?? {}),
      },
    })
    if (!res.ok) {
      let detail = `HTTP ${res.status}`
      try {
        const body = (await res.json()) as { detail?: string }
        if (body.detail) detail = body.detail
      } catch {
        // ignore
      }
      return { data: null, error: detail }
    }
    const data = (await res.json()) as T
    return { data, error: null }
  } catch (e) {
    return { data: null, error: e instanceof Error ? e.message : "Network error" }
  }
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      className="ml-2 text-xs text-muted-foreground hover:text-foreground transition-colors"
      title="Copy to clipboard"
    >
      {copied ? "Copied!" : "Copy"}
    </button>
  )
}

export function AdminInviteCodesPage() {
  const [secret, setSecret] = useState("")
  const [count, setCount] = useState(5)

  const [allCodes, setAllCodes] = useState<InviteCode[] | null>(null)
  const [lastBatch, setLastBatch] = useState<InviteCode[] | null>(null)

  const [loadError, setLoadError] = useState<string | null>(null)
  const [generateError, setGenerateError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isGenerating, setIsGenerating] = useState(false)

  async function loadAllCodes(adminSecret: string) {
    setIsLoading(true)
    setLoadError(null)
    const { data, error } = await apiFetch<{ codes: InviteCode[] }>(
      "/admin/invite-codes",
      adminSecret,
    )
    setIsLoading(false)
    if (error) {
      setLoadError(error)
    } else {
      setAllCodes(data?.codes ?? [])
    }
  }

  async function handleLoad(e: React.FormEvent) {
    e.preventDefault()
    await loadAllCodes(secret)
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault()
    setIsGenerating(true)
    setGenerateError(null)
    const { data, error } = await apiFetch<{ codes: InviteCode[] }>(
      "/admin/invite-codes",
      secret,
      {
        method: "POST",
        body: JSON.stringify({ count }),
      },
    )
    setIsGenerating(false)
    if (error) {
      setGenerateError(error)
    } else {
      setLastBatch(data?.codes ?? [])
      // Refresh the full list
      await loadAllCodes(secret)
    }
  }

  return (
    <div className="space-y-8 max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold">Admin — Invite Codes</h1>

      {/* Secret input */}
      <Card>
        <CardHeader>
          <CardTitle>Admin Secret</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLoad} className="flex gap-3 items-end">
            <div className="flex-1 space-y-1">
              <Label htmlFor="admin-secret">X-Admin-Secret</Label>
              <Input
                id="admin-secret"
                type="password"
                placeholder="Enter admin secret"
                value={secret}
                onChange={(e) => setSecret(e.target.value)}
              />
            </div>
            <Button type="submit" disabled={isLoading || !secret}>
              {isLoading ? "Loading…" : "Load codes"}
            </Button>
          </form>
          {loadError && (
            <p className="mt-2 text-sm text-destructive">{loadError}</p>
          )}
        </CardContent>
      </Card>

      {/* Generate section — only shown after successful secret entry */}
      {allCodes !== null && (
        <>
          <Card>
            <CardHeader>
              <CardTitle>Generate Invite Codes</CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleGenerate} className="flex gap-3 items-end">
                <div className="w-28 space-y-1">
                  <Label htmlFor="count">Count</Label>
                  <Input
                    id="count"
                    type="number"
                    min={1}
                    max={500}
                    value={count}
                    onChange={(e) => setCount(Number(e.target.value))}
                  />
                </div>
                <Button type="submit" disabled={isGenerating}>
                  {isGenerating ? "Generating…" : "Generate"}
                </Button>
              </form>
              {generateError && (
                <p className="mt-2 text-sm text-destructive">{generateError}</p>
              )}

              {lastBatch && lastBatch.length > 0 && (
                <div className="mt-4 space-y-2">
                  <p className="text-sm font-medium text-muted-foreground">
                    Last batch ({lastBatch.length} codes):
                  </p>
                  <ul className="space-y-1">
                    {lastBatch.map((c) => (
                      <li
                        key={c.code_id}
                        className="flex items-center gap-2 rounded bg-muted px-3 py-1.5 font-mono text-sm"
                      >
                        <span className="flex-1">{c.code}</span>
                        <CopyButton text={c.code} />
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>

          {/* All codes table */}
          <Card>
            <CardHeader>
              <CardTitle>All Invite Codes</CardTitle>
            </CardHeader>
            <CardContent>
              {allCodes.length === 0 ? (
                <p className="text-sm text-muted-foreground">No codes yet.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left text-muted-foreground">
                        <th className="pb-2 pr-4 font-medium">Code</th>
                        <th className="pb-2 pr-4 font-medium">Status</th>
                        <th className="pb-2 pr-4 font-medium">Uses left</th>
                        <th className="pb-2 font-medium">Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {allCodes.map((c, i) => (
                        <>
                          {i > 0 && (
                            <tr key={`sep-${c.code_id}`}>
                              <td colSpan={4}>
                                <Separator />
                              </td>
                            </tr>
                          )}
                          <tr key={c.code_id} className="py-1">
                            <td className="py-2 pr-4 font-mono">
                              {c.code}
                              <CopyButton text={c.code} />
                            </td>
                            <td className="py-2 pr-4">
                              {!c.is_active ? (
                                <Badge variant="destructive">Deactivated</Badge>
                              ) : c.uses_left === 0 ? (
                                <Badge variant="secondary">Used</Badge>
                              ) : (
                                <Badge variant="default">Available</Badge>
                              )}
                            </td>
                            <td className="py-2 pr-4 tabular-nums">
                              {c.uses_left} / {c.max_uses}
                            </td>
                            <td className="py-2 text-muted-foreground">
                              {new Date(c.created_at).toLocaleString()}
                            </td>
                          </tr>
                        </>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}

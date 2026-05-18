/**
 * Guarantorship page — bilingual, six sections:
 * 1. My status (outgoing requests + active guarantors)
 * 2. My Guarantorships (as guarantor)
 * 3. Deposits
 * 4. Request a guarantor (by user ID)
 * 5. Incoming requests (accept / reject)
 * 6. Zero Circles (create / join)
 */

import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { useAuthStore } from "@/stores/auth-store"
import {
  useAcceptRequest,
  useCreateDeposit,
  useCreateZeroCircle,
  useIncomingRequests,
  useJoinZeroCircle,
  useMyDeposits,
  useMyGuarantorships,
  useOutgoingRequests,
  useRejectRequest,
  useRequestGuarantor,
  useZeroCircles,
} from "@/hooks/use-guarantorship"
import type {
  DepositCreate,
  GuaranteeRequestResponse,
  GuarantorshipResponse,
  ZeroCircleResponse,
} from "@/api/types"

// ─── Status badge ─────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === "accepted"
      ? "default"
      : status === "rejected"
      ? "destructive"
      : "secondary"
  return <Badge variant={variant}>{status}</Badge>
}

// ─── Request a Guarantor dialog ───────────────────────────────────────────────

function RequestGuarantorDialog() {
  const [open, setOpen] = useState(false)
  const [guarantorId, setGuarantorId] = useState("")
  const [message, setMessage] = useState("")
  const mutation = useRequestGuarantor()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(
      { guarantor_id: guarantorId.trim(), message: message.trim() || null },
      {
        onSuccess: () => {
          setOpen(false)
          setGuarantorId("")
          setMessage("")
        },
      }
    )
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <Button size="sm">Request guarantor / Подать заявку</Button>
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Request a Guarantor / Подать заявку поручителю</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 pt-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="guarantor-id">
              Guarantor User ID / ID поручителя
            </Label>
            <Input
              id="guarantor-id"
              value={guarantorId}
              onChange={(e) => setGuarantorId(e.target.value)}
              placeholder="Enter user ID..."
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="message">
              Message (optional) / Сообщение (необязательно)
            </Label>
            <Textarea
              id="message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Why are you requesting this guarantor?"
              rows={3}
            />
          </div>
          {mutation.isError && (
            <p className="text-sm text-destructive">
              {String((mutation.error as Error)?.message ?? "Error")}
            </p>
          )}
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Sending…" : "Submit / Отправить"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ─── Create Zero Circle dialog ────────────────────────────────────────────────

function CreateCircleDialog() {
  const [open, setOpen] = useState(false)
  const [name, setName] = useState("")
  const [depositStub, setDepositStub] = useState("")
  const mutation = useCreateZeroCircle()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutation.mutate(
      {
        name: name.trim(),
        deposit_stub: depositStub ? parseFloat(depositStub) : null,
      },
      {
        onSuccess: () => {
          setOpen(false)
          setName("")
          setDepositStub("")
        },
      }
    )
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <Button size="sm" variant="outline">
          Create circle / Создать круг
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Create Zero Circle / Создать нулевой круг</DialogTitle>
        </DialogHeader>
        <p className="text-xs text-muted-foreground">
          A zero circle is a mutual-guarantee DAO group. The deposit stub is a
          placeholder — no real funds are transferred yet. The circle will be
          anchored to a DAO contract in the future. /
          Нулевой круг — группа взаимного поручительства DAO. Сумма депозита
          является заглушкой — реальных переводов нет. Круг будет закреплён
          DAO-контрактом в будущем.
        </p>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 pt-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="circle-name">Circle name / Название круга</Label>
            <Input
              id="circle-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Almaty founders circle"
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="deposit-stub">
              Deposit stub (optional) / Сумма депозита (заглушка)
            </Label>
            <Input
              id="deposit-stub"
              type="number"
              min="0.01"
              step="0.01"
              value={depositStub}
              onChange={(e) => setDepositStub(e.target.value)}
              placeholder="100.00"
            />
          </div>
          {mutation.isError && (
            <p className="text-sm text-destructive">
              {String((mutation.error as Error)?.message ?? "Error")}
            </p>
          )}
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Creating…" : "Create / Создать"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ─── Zero Circle card ─────────────────────────────────────────────────────────

function ZeroCircleCard({
  circle,
  currentUserId,
}: {
  circle: ZeroCircleResponse
  currentUserId: string
}) {
  const joinMutation = useJoinZeroCircle()
  const isMember = circle.members.some((m) => m.user_id === currentUserId)

  return (
    <div className="rounded-md border p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="font-medium">{circle.name}</span>
        <Badge variant="secondary">{circle.members.length} members</Badge>
      </div>
      {circle.deposit_stub != null && (
        <p className="text-xs text-muted-foreground">
          Deposit stub / Депозит: {circle.deposit_stub}
        </p>
      )}
      <p className="text-xs text-muted-foreground">
        Initiated by / Основатель: <code>{circle.initiated_by}</code>
      </p>
      {!isMember && (
        <Button
          size="sm"
          variant="outline"
          disabled={joinMutation.isPending}
          onClick={() => joinMutation.mutate(circle.circle_id)}
        >
          {joinMutation.isPending ? "Joining…" : "Join / Вступить"}
        </Button>
      )}
      {isMember && (
        <span className="text-xs text-muted-foreground italic">
          You are a member / Вы участник
        </span>
      )}
    </div>
  )
}

// ─── Create Deposit dialog ────────────────────────────────────────────────────

function CreateDepositDialog() {
  const [open, setOpen] = useState(false)
  const [guarantorId, setGuarantorId] = useState("")
  const [amount, setAmount] = useState("")
  const [blockchainRef, setBlockchainRef] = useState("")
  const mutation = useCreateDeposit()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const body: DepositCreate = {
      guarantor_id: guarantorId.trim(),
      amount: parseFloat(amount),
      blockchain_ref: blockchainRef.trim() || null,
    }
    mutation.mutate(body, {
      onSuccess: () => {
        setOpen(false)
        setGuarantorId("")
        setAmount("")
        setBlockchainRef("")
      },
    })
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <Button size="sm">Add deposit / Добавить депозит</Button>
      </DialogTrigger>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>Create Deposit / Создать депозит</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 pt-2">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="dep-guarantor-id">
              Guarantor User ID / ID поручителя
            </Label>
            <Input
              id="dep-guarantor-id"
              value={guarantorId}
              onChange={(e) => setGuarantorId(e.target.value)}
              placeholder="Enter guarantor ID..."
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="dep-amount">Amount / Сумма</Label>
            <Input
              id="dep-amount"
              type="number"
              min="0.01"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="100.00"
              required
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="dep-blockchain-ref">
              Blockchain ref (optional) / Блокчейн-ссылка (необязательно)
            </Label>
            <Input
              id="dep-blockchain-ref"
              value={blockchainRef}
              onChange={(e) => setBlockchainRef(e.target.value)}
              placeholder="0x..."
            />
          </div>
          {mutation.isError && (
            <p className="text-sm text-destructive">
              {String((mutation.error as Error)?.message ?? "Error")}
            </p>
          )}
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? "Creating…" : "Create / Создать"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────────

export function GuarantorshipPage() {
  const currentUserId = useAuthStore((s) => s.userId)

  const incomingQuery = useIncomingRequests()
  const outgoingQuery = useOutgoingRequests()
  const circlesQuery = useZeroCircles()
  const guarantorshipsQuery = useMyGuarantorships()
  const depositsQuery = useMyDeposits()

  const acceptMutation = useAcceptRequest()
  const rejectMutation = useRejectRequest()

  const activeGuarantors =
    outgoingQuery.data?.filter((r: GuaranteeRequestResponse) => r.status === "accepted") ?? []
  const pendingOutgoing =
    outgoingQuery.data?.filter((r: GuaranteeRequestResponse) => r.status === "pending") ?? []
  const pendingIncoming =
    incomingQuery.data?.filter((r: GuaranteeRequestResponse) => r.status === "pending") ?? []

  return (
    <div className="container py-8 max-w-2xl flex flex-col gap-8">

      {/* Header */}
      <div>
        <h1 className="text-2xl font-semibold">
          Guarantorship / Поручительство
        </h1>
        <div className="mt-3 flex flex-col gap-2 text-sm leading-relaxed text-muted-foreground">
          <p>
            Every deal on CollabHub is protected by a guarantee deposit held by
            two trusted guarantors. The deposit defines your{" "}
            <em>action quantum</em> — the maximum value of a single
            fully-insured transaction.
          </p>
          <p>
            Каждая сделка защищена гарантийным депозитом у двух доверенных
            поручителей. Депозит определяет ваш <em>квант действия</em> —
            максимальную сумму одной застрахованной сделки.
          </p>
        </div>
      </div>

      {/* Section 1: My status */}
      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">
          My status / Мой статус
        </h2>
        {activeGuarantors.length > 0 ? (
          <div className="flex flex-col gap-2">
            {activeGuarantors.map((r) => (
              <div
                key={r.request_id}
                className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
              >
                <span>
                  Guarantor / Поручитель:{" "}
                  <code className="text-xs">{r.guarantor_id}</code>
                </span>
                <StatusBadge status={r.status} />
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            You have no active guarantors yet. /
            У вас ещё нет активных поручителей.
          </p>
        )}

        {pendingOutgoing.length > 0 && (
          <div className="flex flex-col gap-1.5">
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide">
              Pending / В ожидании
            </p>
            {pendingOutgoing.map((r) => (
              <div
                key={r.request_id}
                className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
              >
                <span>
                  → <code className="text-xs">{r.guarantor_id}</code>
                </span>
                <StatusBadge status={r.status} />
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Section 2: My Guarantorships (as guarantor) */}
      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">
          My wards / Мои подопечные
        </h2>
        <p className="text-sm text-muted-foreground">
          Users for whom you are an active guarantor. /
          Пользователи, для которых вы являетесь активным поручителем.
        </p>
        {guarantorshipsQuery.isLoading && (
          <p className="text-sm text-muted-foreground">Loading… / Загрузка…</p>
        )}
        {guarantorshipsQuery.data?.length === 0 && (
          <p className="text-sm text-muted-foreground">
            You are not guaranteeing anyone yet. /
            Вы пока не поручаетесь ни за кого.
          </p>
        )}
        {guarantorshipsQuery.data && guarantorshipsQuery.data.length > 0 && (
          <div className="flex flex-col gap-2">
            {guarantorshipsQuery.data.map((g: GuarantorshipResponse) => (
              <div
                key={g.guarantorship_id}
                className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
              >
                <span>
                  Ward / Подопечный:{" "}
                  <code className="text-xs">{g.ward_id}</code>
                </span>
                <span className="text-xs text-muted-foreground">
                  {new Date(g.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Section 3: Deposits */}
      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">
            Deposits / Депозиты
          </h2>
          <CreateDepositDialog />
        </div>
        <p className="text-sm text-muted-foreground">
          Deposits you have placed with your guarantors. /
          Депозиты, размещённые у ваших поручителей.
        </p>
        {depositsQuery.isLoading && (
          <p className="text-sm text-muted-foreground">Loading… / Загрузка…</p>
        )}
        {depositsQuery.data?.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No deposits yet. / Депозитов пока нет.
          </p>
        )}
        {depositsQuery.data && depositsQuery.data.length > 0 && (
          <div className="flex flex-col gap-2">
            {depositsQuery.data.map((d) => (
              <div
                key={d.deposit_id}
                className="rounded-md border px-3 py-2 text-sm flex items-center justify-between"
              >
                <div className="flex flex-col gap-0.5">
                  <span>
                    Guarantor:{" "}
                    <code className="text-xs">{d.guarantor_id}</code>
                  </span>
                  {d.blockchain_ref && (
                    <span className="text-xs text-muted-foreground">
                      ref: {d.blockchain_ref}
                    </span>
                  )}
                </div>
                <Badge variant="secondary">{d.amount}</Badge>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Section 4: Request a guarantor */}
      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">
            Find a guarantor / Найти поручителя
          </h2>
          <RequestGuarantorDialog />
        </div>
        <p className="text-sm text-muted-foreground">
          Enter the user ID of the person you want to act as your guarantor.
          They will receive an incoming request to accept or reject. /
          Введите ID пользователя, которого хотите попросить стать вашим
          поручителем. Он получит запрос на принятие или отклонение.
        </p>
      </section>

      {/* Section 5: Incoming requests */}
      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">
          Incoming requests / Входящие заявки
        </h2>
        {pendingIncoming.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No pending incoming requests. / Нет входящих заявок.
          </p>
        ) : (
          <div className="flex flex-col gap-2">
            {pendingIncoming.map((r) => (
              <div
                key={r.request_id}
                className="rounded-md border p-3 flex flex-col gap-2 text-sm"
              >
                <div className="flex items-center justify-between">
                  <span>
                    From / От:{" "}
                    <code className="text-xs">{r.ward_id}</code>
                  </span>
                  <StatusBadge status={r.status} />
                </div>
                {r.message && (
                  <p className="text-muted-foreground text-xs italic">
                    "{r.message}"
                  </p>
                )}
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    disabled={acceptMutation.isPending}
                    onClick={() => acceptMutation.mutate(r.request_id)}
                  >
                    Accept / Принять
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={rejectMutation.isPending}
                    onClick={() => rejectMutation.mutate(r.request_id)}
                  >
                    Reject / Отклонить
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Section 6: Zero Circles */}
      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">
            Zero Circles / Нулевые круги
          </h2>
          <CreateCircleDialog />
        </div>
        <p className="text-sm text-muted-foreground">
          No guarantors with deposits available? Form a Zero Circle — a mutual
          DAO group that commits to guarantorship collectively. Deposits are
          stubs for now and will be anchored to a DAO contract in the future. /
          Нет поручителей с депозитами? Создайте нулевой круг — группу
          взаимного поручительства DAO. Депозиты пока являются заглушками и
          будут закреплены DAO-контрактом в будущем.
        </p>

        {circlesQuery.isLoading && (
          <p className="text-sm text-muted-foreground">Loading… / Загрузка…</p>
        )}

        {circlesQuery.data?.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No open circles yet. Be the first! /
            Открытых кругов пока нет. Будьте первым!
          </p>
        )}

        {circlesQuery.data && circlesQuery.data.length > 0 && (
          <div className="flex flex-col gap-3">
            {circlesQuery.data.map((circle) => (
              <ZeroCircleCard
                key={circle.circle_id}
                circle={circle}
                currentUserId={currentUserId ?? ""}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

export function GuarantorshipPage() {
  return (
    <div className="container py-8 max-w-2xl">
      <h1 className="text-2xl font-semibold">Guarantorship / Поручительство</h1>

      <div className="mt-6 flex flex-col gap-4 text-sm leading-relaxed text-foreground">
        <p>
          Every deal on CollabHub is protected by a guarantee deposit held by two trusted
          guarantors. The deposit defines your <em>action quantum</em> — the maximum value
          of a single fully-insured transaction. Act as a guarantor for others, manage your
          own deposit, and transact with confidence knowing every exchange is backed by a
          mutual guarantee system.
        </p>
        <p className="text-muted-foreground">
          Каждая сделка в CollabHub защищена гарантийным депозитом, который хранится у двух
          доверенных поручителей. Депозит определяет ваш <em>квант действия</em> —
          максимальную сумму одной полностью застрахованной сделки. Выступайте гарантом для
          других, управляйте своим депозитом и заключайте сделки с уверенностью — каждый
          обмен обеспечен системой взаимного поручительства.
        </p>
      </div>

      <div className="mt-8 rounded-md border border-yellow-400/40 bg-yellow-50/10 px-4 py-3 text-sm text-yellow-600 dark:text-yellow-400">
        🚧 This feature is currently under development. Stay tuned. /
        Функция находится в разработке. Следите за обновлениями.
      </div>
    </div>
  )
}

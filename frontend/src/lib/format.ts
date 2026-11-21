// Display formatting helpers. Money arrives from the API as strings; these turn them into
// readable currency without losing the original precision until the final render.

export function formatMoney(amount: string | number | null | undefined, currency?: string | null): string {
  if (amount === null || amount === undefined || amount === '') return '—'
  const value = typeof amount === 'string' ? Number(amount) : amount
  if (Number.isNaN(value)) return '—'
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
      maximumFractionDigits: 0,
    }).format(value)
  } catch {
    // Unknown currency code — fall back to a plain number with the code appended.
    return `${value.toLocaleString('en-US', { maximumFractionDigits: 0 })} ${currency ?? ''}`.trim()
  }
}

export function formatUsd(amount: string | number | null | undefined): string {
  return formatMoney(amount, 'USD')
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

const STATUS_LABELS: Record<string, string> = {
  active: 'Active',
  on_leave: 'On leave',
  terminated: 'Terminated',
}

export function statusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status
}

const REASON_LABELS: Record<string, string> = {
  hire: 'Hire',
  raise: 'Raise',
  promotion: 'Promotion',
  adjustment: 'Adjustment',
}

export function reasonLabel(reason: string): string {
  return REASON_LABELS[reason] ?? reason
}

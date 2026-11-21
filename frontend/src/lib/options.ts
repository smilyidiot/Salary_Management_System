// Builders that turn reference data into Mantine Select option lists.

import type { ReferenceData } from '../api/types'

export const PAY_FREQUENCY_OPTIONS = [
  { value: 'annual', label: 'Annual' },
  { value: 'monthly', label: 'Monthly' },
]

export const REASON_OPTIONS = [
  { value: 'hire', label: 'Hire' },
  { value: 'raise', label: 'Raise' },
  { value: 'promotion', label: 'Promotion' },
  { value: 'adjustment', label: 'Adjustment' },
]

export const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'on_leave', label: 'On leave' },
  { value: 'terminated', label: 'Terminated' },
]

export function countryOptions(ref: ReferenceData | null) {
  return (ref?.countries ?? []).map((c) => ({ value: c.code, label: `${c.name} (${c.code})` }))
}

export function departmentOptions(ref: ReferenceData | null) {
  return (ref?.departments ?? []).map((d) => ({ value: d, label: d }))
}

export function levelOptions(ref: ReferenceData | null) {
  return (ref?.levels ?? []).map((l) => ({ value: l, label: l }))
}

export function currencyOptions(ref: ReferenceData | null) {
  const seen = new Set<string>()
  const out: { value: string; label: string }[] = []
  for (const c of ref?.countries ?? []) {
    if (!seen.has(c.currency)) {
      seen.add(c.currency)
      out.push({ value: c.currency, label: c.currency })
    }
  }
  return out
}

export function currencyForCountry(ref: ReferenceData | null, code: string | null): string | null {
  if (!code) return null
  return ref?.countries.find((c) => c.code === code)?.currency ?? null
}

import { describe, expect, it } from 'vitest'

import { formatDate, formatMoney, formatUsd, reasonLabel, statusLabel } from './format'

describe('formatMoney', () => {
  it('formats a string amount as USD', () => {
    expect(formatUsd('80000')).toBe('$80,000')
  })

  it('formats a non-USD currency', () => {
    expect(formatMoney('74600', 'EUR')).toBe('€74,600')
  })

  it('rounds to whole units', () => {
    expect(formatUsd('14400.03')).toBe('$14,400')
  })

  it('returns an em dash for null/empty', () => {
    expect(formatMoney(null)).toBe('—')
    expect(formatMoney('')).toBe('—')
  })

  it('falls back gracefully for an unknown currency code', () => {
    expect(formatMoney('1000', 'ZZZ')).toContain('1,000')
  })
})

describe('labels', () => {
  it('humanizes employment status', () => {
    expect(statusLabel('on_leave')).toBe('On leave')
    expect(statusLabel('active')).toBe('Active')
  })

  it('humanizes compensation reason', () => {
    expect(reasonLabel('raise')).toBe('Raise')
  })
})

describe('formatDate', () => {
  it('formats an ISO date', () => {
    expect(formatDate('2020-06-15')).toContain('2020')
  })

  it('returns an em dash for empty input', () => {
    expect(formatDate(null)).toBe('—')
  })
})

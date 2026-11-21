import userEvent from '@testing-library/user-event'
import { screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '../test/render'
import type { PaginatedEmployees } from '../api/types'
import { EmployeesPage } from './EmployeesPage'

// Mock the API and reference data so the test is deterministic and offline.
const listEmployees = vi.fn()

vi.mock('../api/client', () => ({
  api: {
    listEmployees: (...args: unknown[]) => listEmployees(...args),
    exportCsvUrl: () => '/api/employees/export.csv',
  },
  ApiError: class ApiError extends Error {},
}))

vi.mock('../api/ReferenceContext', () => ({
  useReference: () => ({
    countries: [{ code: 'US', name: 'United States', currency: 'USD' }],
    departments: ['Engineering'],
    levels: ['L1'],
    employment_statuses: [],
    pay_frequencies: [],
    compensation_reasons: [],
  }),
}))

const page = (overrides: Partial<PaginatedEmployees> = {}): PaginatedEmployees => ({
  items: [
    {
      id: 1,
      employee_code: 'E00001',
      full_name: 'Ada Lovelace',
      email: 'ada@acme.co',
      country: 'US',
      department: 'Engineering',
      job_title: 'Software Engineer',
      level: 'L4',
      employment_status: 'active',
      manager_id: null,
      current_salary: '120000',
      currency: 'USD',
      current_salary_usd: '120000.00',
    },
  ],
  total: 1,
  page: 1,
  page_size: 25,
  pages: 1,
  ...overrides,
})

beforeEach(() => {
  listEmployees.mockReset()
  listEmployees.mockResolvedValue(page())
})

describe('EmployeesPage', () => {
  it('renders employees returned by the API', async () => {
    renderWithProviders(<EmployeesPage />)
    expect(await screen.findByText('Ada Lovelace')).toBeInTheDocument()
    expect(screen.getByText('1 employees')).toBeInTheDocument()
  })

  it('refetches with the search term as a query param', async () => {
    renderWithProviders(<EmployeesPage />)
    await screen.findByText('Ada Lovelace')

    const input = screen.getByPlaceholderText('Name, code, or email')
    await userEvent.type(input, 'Ada')

    await waitFor(() =>
      expect(listEmployees).toHaveBeenCalledWith(expect.objectContaining({ q: 'Ada' })),
    )
  })

  it('shows an empty state when there are no matches', async () => {
    listEmployees.mockResolvedValue(page({ items: [], total: 0, pages: 0 }))
    renderWithProviders(<EmployeesPage />)
    expect(await screen.findByText(/no employees match/i)).toBeInTheDocument()
  })
})

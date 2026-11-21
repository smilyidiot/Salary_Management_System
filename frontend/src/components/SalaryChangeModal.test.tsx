import userEvent from '@testing-library/user-event'
import { screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { renderWithProviders } from '../test/render'
import type { EmployeeDetail } from '../api/types'
import { SalaryChangeModal } from './SalaryChangeModal'

const addCompensation = vi.fn()

vi.mock('../api/client', () => ({
  api: { addCompensation: (...args: unknown[]) => addCompensation(...args) },
  ApiError: class ApiError extends Error {},
}))

vi.mock('../api/ReferenceContext', () => ({
  useReference: () => ({
    countries: [{ code: 'US', name: 'United States', currency: 'USD' }],
    departments: [],
    levels: [],
    employment_statuses: [],
    pay_frequencies: [],
    compensation_reasons: [],
  }),
}))

vi.mock('@mantine/notifications', () => ({ notifications: { show: vi.fn() } }))

const employee: EmployeeDetail = {
  id: 1,
  employee_code: 'E00001',
  full_name: 'Ada Lovelace',
  email: 'ada@acme.co',
  country: 'US',
  department: 'Engineering',
  job_title: 'Software Engineer',
  level: 'L4',
  manager_id: null,
  hire_date: '2020-01-01',
  employment_status: 'active',
  manager: null,
  compensation_records: [],
  current_salary: '100000',
  currency: 'USD',
  current_salary_usd: '100000.00',
}

beforeEach(() => addCompensation.mockReset())

describe('SalaryChangeModal', () => {
  it('blocks submission and shows an error when the amount is missing', async () => {
    renderWithProviders(
      <SalaryChangeModal employee={employee} opened onClose={() => {}} onSaved={() => {}} />,
    )

    await userEvent.click(screen.getByRole('button', { name: /record change/i }))

    expect(await screen.findByText(/greater than 0/i)).toBeInTheDocument()
    expect(addCompensation).not.toHaveBeenCalled()
  })

  it('submits a valid salary change to the API', async () => {
    addCompensation.mockResolvedValue({ ...employee })
    renderWithProviders(
      <SalaryChangeModal employee={employee} opened onClose={() => {}} onSaved={() => {}} />,
    )

    await userEvent.type(screen.getByLabelText(/amount/i), '125000')
    await userEvent.click(screen.getByRole('button', { name: /record change/i }))

    await waitFor(() => expect(addCompensation).toHaveBeenCalledTimes(1))
    expect(addCompensation).toHaveBeenCalledWith(
      1,
      expect.objectContaining({ base_amount: '125000', currency: 'USD', reason: 'raise' }),
    )
  })
})

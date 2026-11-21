// TypeScript mirrors of the backend Pydantic schemas.
//
// These are hand-written rather than code-generated — a deliberate simplicity trade-off
// for a project this size (see docs/DECISIONS.md). Money fields arrive as strings from the
// API (the backend serializes Decimal as a precision-safe string), so they are typed as
// `string` and formatted at the display layer.

export type EmploymentStatus = 'active' | 'on_leave' | 'terminated'
export type PayFrequency = 'annual' | 'monthly'
export type CompensationReason = 'hire' | 'raise' | 'promotion' | 'adjustment'

export interface CompensationRecord {
  id: number
  base_amount: string
  currency: string
  pay_frequency: PayFrequency
  effective_from: string
  reason: CompensationReason
}

export interface CompensationCreate {
  base_amount: string
  currency: string
  pay_frequency: PayFrequency
  effective_from: string
  reason: CompensationReason
}

export interface ManagerRef {
  id: number
  employee_code: string
  full_name: string
}

export interface EmployeeListItem {
  id: number
  employee_code: string
  full_name: string
  email: string
  country: string
  department: string
  job_title: string
  level: string
  employment_status: EmploymentStatus
  manager_id: number | null
  current_salary: string | null
  currency: string | null
  current_salary_usd: string | null
}

export interface EmployeeDetail {
  id: number
  employee_code: string
  full_name: string
  email: string
  country: string
  department: string
  job_title: string
  level: string
  manager_id: number | null
  hire_date: string
  employment_status: EmploymentStatus
  manager: ManagerRef | null
  compensation_records: CompensationRecord[]
  current_salary: string | null
  currency: string | null
  current_salary_usd: string | null
}

export interface EmployeeCreate {
  full_name: string
  email: string
  country: string
  department: string
  job_title: string
  level: string
  manager_id: number | null
  hire_date: string
  employment_status: EmploymentStatus
  initial_compensation: CompensationCreate
}

export type EmployeeUpdate = Partial<Omit<EmployeeCreate, 'initial_compensation'>>

export interface PaginatedEmployees {
  items: EmployeeListItem[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface GroupStat {
  key: string
  label: string
  headcount: number
  avg_salary_usd: string
  median_salary_usd: string
  total_payroll_usd: string
}

export interface StatusCount {
  status: EmploymentStatus
  count: number
}

export interface DistributionBucket {
  label: string
  min_usd: number
  max_usd: number | null
  count: number
}

export interface AnalyticsSummary {
  total_headcount: number
  workforce_headcount: number
  total_payroll_usd: string
  average_salary_usd: string
  median_salary_usd: string
  by_status: StatusCount[]
}

export interface ReferenceData {
  countries: { code: string; name: string; currency: string }[]
  departments: string[]
  levels: string[]
  employment_statuses: EmploymentStatus[]
  pay_frequencies: PayFrequency[]
  compensation_reasons: CompensationReason[]
}

export interface EmployeeQuery {
  q?: string
  country?: string
  department?: string
  employment_status?: EmploymentStatus
  sort?: string
  order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

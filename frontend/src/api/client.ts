// Thin typed API client. One place that knows how to talk to the backend, so components
// never hand-build URLs or parse responses. Throws `ApiError` on non-2xx so callers can
// surface the backend's error message.

import type {
  AnalyticsSummary,
  CompensationCreate,
  DistributionBucket,
  EmployeeCreate,
  EmployeeDetail,
  EmployeeQuery,
  EmployeeUpdate,
  GroupStat,
  PaginatedEmployees,
  ReferenceData,
} from './types'

const BASE = '/api'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

function queryString(params: Record<string, unknown>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value))
    }
  }
  const s = search.toString()
  return s ? `?${s}` : ''
}

export const api = {
  reference: () => request<ReferenceData>('/reference'),

  listEmployees: (query: EmployeeQuery = {}) =>
    request<PaginatedEmployees>(`/employees${queryString(query as Record<string, unknown>)}`),

  getEmployee: (id: number) => request<EmployeeDetail>(`/employees/${id}`),

  createEmployee: (payload: EmployeeCreate) =>
    request<EmployeeDetail>('/employees', { method: 'POST', body: JSON.stringify(payload) }),

  updateEmployee: (id: number, payload: EmployeeUpdate) =>
    request<EmployeeDetail>(`/employees/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),

  addCompensation: (id: number, payload: CompensationCreate) =>
    request<EmployeeDetail>(`/employees/${id}/compensation`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  exportCsvUrl: (query: EmployeeQuery = {}) =>
    `${BASE}/employees/export.csv${queryString(query as Record<string, unknown>)}`,

  analyticsSummary: () => request<AnalyticsSummary>('/analytics/summary'),
  analyticsByCountry: () => request<GroupStat[]>('/analytics/by-country'),
  analyticsByDepartment: () => request<GroupStat[]>('/analytics/by-department'),
  analyticsDistribution: () => request<DistributionBucket[]>('/analytics/distribution'),
}

// Employee directory: server-side search, filtering, sorting, and pagination over the
// full population. The UI only ever holds one page of rows at a time.

import {
  Alert,
  Anchor,
  Box,
  Button,
  Center,
  Group,
  Loader,
  Pagination,
  Paper,
  Select,
  Table,
  Text,
  TextInput,
  Title,
  UnstyledButton,
} from '@mantine/core'
import { useDebouncedValue } from '@mantine/hooks'
import {
  IconChevronDown,
  IconChevronUp,
  IconDownload,
  IconPlus,
  IconSearch,
  IconSelector,
} from '@tabler/icons-react'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { api, ApiError } from '../api/client'
import { useReference } from '../api/ReferenceContext'
import type { EmploymentStatus, PaginatedEmployees } from '../api/types'
import { StatusBadge } from '../components/StatusBadge'
import { formatMoney, formatUsd } from '../lib/format'

const PAGE_SIZE = 25

interface SortState {
  field: string
  order: 'asc' | 'desc'
}

function SortableTh({
  label,
  field,
  sort,
  onSort,
  numeric,
}: {
  label: string
  field: string
  sort: SortState
  onSort: (field: string) => void
  numeric?: boolean
}) {
  const active = sort.field === field
  const Icon = active ? (sort.order === 'asc' ? IconChevronUp : IconChevronDown) : IconSelector
  return (
    <Table.Th style={{ textAlign: numeric ? 'right' : 'left' }}>
      <UnstyledButton onClick={() => onSort(field)} style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
        <Text fw={600} size="sm">
          {label}
        </Text>
        <Icon size={14} opacity={active ? 1 : 0.4} />
      </UnstyledButton>
    </Table.Th>
  )
}

export function EmployeesPage() {
  const navigate = useNavigate()
  const reference = useReference()

  const [search, setSearch] = useState('')
  const [debouncedSearch] = useDebouncedValue(search, 300)
  const [country, setCountry] = useState<string | null>(null)
  const [department, setDepartment] = useState<string | null>(null)
  const [status, setStatus] = useState<string | null>(null)
  const [sort, setSort] = useState<SortState>({ field: 'full_name', order: 'asc' })
  const [page, setPage] = useState(1)

  const [data, setData] = useState<PaginatedEmployees | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const query = useMemo(
    () => ({
      q: debouncedSearch || undefined,
      country: country || undefined,
      department: department || undefined,
      employment_status: (status as EmploymentStatus) || undefined,
      sort: sort.field,
      order: sort.order,
      page,
      page_size: PAGE_SIZE,
    }),
    [debouncedSearch, country, department, status, sort, page],
  )

  // Reset to the first page whenever the result set changes (not when paging).
  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, country, department, status, sort])

  useEffect(() => {
    let active = true
    setLoading(true)
    api
      .listEmployees(query)
      .then((res) => {
        if (active) {
          setData(res)
          setError(null)
        }
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof ApiError ? err.message : 'Failed to load employees')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [query])

  const handleSort = (field: string) => {
    setSort((prev) =>
      prev.field === field ? { field, order: prev.order === 'asc' ? 'desc' : 'asc' } : { field, order: 'asc' },
    )
  }

  const countryOptions = (reference?.countries ?? []).map((c) => ({ value: c.code, label: c.name }))
  const departmentOptions = (reference?.departments ?? []).map((d) => ({ value: d, label: d }))
  const statusOptions = [
    { value: 'active', label: 'Active' },
    { value: 'on_leave', label: 'On leave' },
    { value: 'terminated', label: 'Terminated' },
  ]

  return (
    <>
      <Group justify="space-between" mb="md">
        <Title order={2}>Employees</Title>
        <Group>
          <Button
            component="a"
            href={api.exportCsvUrl({ ...query, page: undefined, page_size: undefined })}
            variant="default"
            leftSection={<IconDownload size={16} />}
          >
            Export CSV
          </Button>
          <Button leftSection={<IconPlus size={16} />} onClick={() => navigate('/employees/new')}>
            Add employee
          </Button>
        </Group>
      </Group>

      <Paper withBorder p="md" mb="md">
        <Group align="end" gap="sm">
          <TextInput
            label="Search"
            placeholder="Name, code, or email"
            leftSection={<IconSearch size={16} />}
            value={search}
            onChange={(e) => setSearch(e.currentTarget.value)}
            style={{ flex: 1, minWidth: 220 }}
          />
          <Select
            label="Country"
            placeholder="All"
            data={countryOptions}
            value={country}
            onChange={setCountry}
            clearable
            searchable
            w={160}
          />
          <Select
            label="Department"
            placeholder="All"
            data={departmentOptions}
            value={department}
            onChange={setDepartment}
            clearable
            w={180}
          />
          <Select
            label="Status"
            placeholder="All"
            data={statusOptions}
            value={status}
            onChange={setStatus}
            clearable
            w={150}
          />
        </Group>
      </Paper>

      {error && (
        <Alert color="red" mb="md">
          {error}
        </Alert>
      )}

      <Paper withBorder pos="relative">
        <Table.ScrollContainer minWidth={900}>
          <Table highlightOnHover verticalSpacing="sm">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Code</Table.Th>
                <SortableTh label="Name" field="full_name" sort={sort} onSort={handleSort} />
                <SortableTh label="Country" field="country" sort={sort} onSort={handleSort} />
                <SortableTh label="Department" field="department" sort={sort} onSort={handleSort} />
                <Table.Th>Title</Table.Th>
                <SortableTh label="Level" field="level" sort={sort} onSort={handleSort} />
                <Table.Th>Status</Table.Th>
                <SortableTh
                  label="Current salary (USD)"
                  field="current_salary_usd"
                  sort={sort}
                  onSort={handleSort}
                  numeric
                />
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {data?.items.map((emp) => (
                <Table.Tr
                  key={emp.id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => navigate(`/employees/${emp.id}`)}
                >
                  <Table.Td>
                    <Anchor component="span" size="sm">
                      {emp.employee_code}
                    </Anchor>
                  </Table.Td>
                  <Table.Td>{emp.full_name}</Table.Td>
                  <Table.Td>{emp.country}</Table.Td>
                  <Table.Td>{emp.department}</Table.Td>
                  <Table.Td>{emp.job_title}</Table.Td>
                  <Table.Td>{emp.level}</Table.Td>
                  <Table.Td>
                    <StatusBadge status={emp.employment_status} />
                  </Table.Td>
                  <Table.Td style={{ textAlign: 'right' }}>
                    <Text size="sm">{formatUsd(emp.current_salary_usd)}</Text>
                    <Text size="xs" c="dimmed">
                      {formatMoney(emp.current_salary, emp.currency)} {emp.currency}
                    </Text>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>

        {loading && (
          <Center p="xl">
            <Loader size="sm" />
          </Center>
        )}

        {!loading && data?.items.length === 0 && (
          <Center p="xl">
            <Text c="dimmed">No employees match these filters.</Text>
          </Center>
        )}
      </Paper>

      <Group justify="space-between" mt="md">
        <Text size="sm" c="dimmed">
          {data ? `${data.total.toLocaleString()} employees` : ' '}
        </Text>
        {data && data.pages > 1 && (
          <Pagination value={page} onChange={setPage} total={data.pages} siblings={1} />
        )}
      </Group>
      <Box h={8} />
    </>
  )
}

// Employee profile: identity, current salary, and the full effective-dated salary history,
// with actions to edit the profile or record a salary change.

import {
  Alert,
  Anchor,
  Badge,
  Box,
  Button,
  Card,
  Center,
  Grid,
  Group,
  Loader,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { useDisclosure } from '@mantine/hooks'
import { IconArrowLeft, IconEdit, IconPlus } from '@tabler/icons-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api, ApiError } from '../api/client'
import type { EmployeeDetail } from '../api/types'
import { EditEmployeeModal } from '../components/EditEmployeeModal'
import { SalaryChangeModal } from '../components/SalaryChangeModal'
import { StatusBadge } from '../components/StatusBadge'
import { formatDate, formatMoney, formatUsd, reasonLabel } from '../lib/format'

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <Box>
      <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
        {label}
      </Text>
      <Text size="sm">{children}</Text>
    </Box>
  )
}

export function EmployeeDetailPage() {
  const { id } = useParams()
  const [employee, setEmployee] = useState<EmployeeDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editOpen, editHandlers] = useDisclosure(false)
  const [salaryOpen, salaryHandlers] = useDisclosure(false)

  useEffect(() => {
    let active = true
    setLoading(true)
    api
      .getEmployee(Number(id))
      .then((res) => {
        if (active) {
          setEmployee(res)
          setError(null)
        }
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof ApiError ? err.message : 'Failed to load employee')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [id])

  if (loading) {
    return (
      <Center p="xl">
        <Loader />
      </Center>
    )
  }

  if (error || !employee) {
    return (
      <>
        <BackLink />
        <Alert color="red" mt="md">
          {error ?? 'Employee not found'}
        </Alert>
      </>
    )
  }

  // History newest-first; the first row is the current compensation.
  const history = [...employee.compensation_records].sort((a, b) =>
    b.effective_from.localeCompare(a.effective_from),
  )

  return (
    <>
      <BackLink />

      <Group justify="space-between" mt="sm" mb="md" align="flex-start">
        <Box>
          <Group gap="sm">
            <Title order={2}>{employee.full_name}</Title>
            <StatusBadge status={employee.employment_status} />
          </Group>
          <Text c="dimmed">
            {employee.employee_code} · {employee.job_title} · {employee.level}
          </Text>
        </Box>
        <Group>
          <Button variant="default" leftSection={<IconEdit size={16} />} onClick={editHandlers.open}>
            Edit
          </Button>
          <Button leftSection={<IconPlus size={16} />} onClick={salaryHandlers.open}>
            Record salary change
          </Button>
        </Group>
      </Group>

      <Grid>
        <Grid.Col span={{ base: 12, md: 7 }}>
          <Card withBorder h="100%">
            <Title order={4} mb="md">
              Profile
            </Title>
            <Grid>
              <Grid.Col span={6}>
                <Field label="Email">{employee.email}</Field>
              </Grid.Col>
              <Grid.Col span={6}>
                <Field label="Country">{employee.country}</Field>
              </Grid.Col>
              <Grid.Col span={6}>
                <Field label="Department">{employee.department}</Field>
              </Grid.Col>
              <Grid.Col span={6}>
                <Field label="Level">{employee.level}</Field>
              </Grid.Col>
              <Grid.Col span={6}>
                <Field label="Hire date">{formatDate(employee.hire_date)}</Field>
              </Grid.Col>
              <Grid.Col span={6}>
                <Field label="Manager">
                  {employee.manager ? (
                    <Anchor component={Link} to={`/employees/${employee.manager.id}`}>
                      {employee.manager.full_name}
                    </Anchor>
                  ) : (
                    '—'
                  )}
                </Field>
              </Grid.Col>
            </Grid>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 5 }}>
          <Card withBorder h="100%">
            <Title order={4} mb="md">
              Current salary
            </Title>
            <Text size="xl" fw={700}>
              {formatUsd(employee.current_salary_usd)}
            </Text>
            <Text c="dimmed">
              {formatMoney(employee.current_salary, employee.currency)} {employee.currency} / year
            </Text>
          </Card>
        </Grid.Col>
      </Grid>

      <Card withBorder mt="md">
        <Title order={4} mb="md">
          Salary history
        </Title>
        <Table>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Effective from</Table.Th>
              <Table.Th>Amount</Table.Th>
              <Table.Th>Frequency</Table.Th>
              <Table.Th>Reason</Table.Th>
              <Table.Th />
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {history.map((rec, idx) => (
              <Table.Tr key={rec.id}>
                <Table.Td>{formatDate(rec.effective_from)}</Table.Td>
                <Table.Td>
                  {formatMoney(rec.base_amount, rec.currency)} {rec.currency}
                </Table.Td>
                <Table.Td tt="capitalize">{rec.pay_frequency}</Table.Td>
                <Table.Td>{reasonLabel(rec.reason)}</Table.Td>
                <Table.Td>
                  {idx === 0 && (
                    <Badge color="blue" variant="light">
                      Current
                    </Badge>
                  )}
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Card>

      <SalaryChangeModal
        employee={employee}
        opened={salaryOpen}
        onClose={salaryHandlers.close}
        onSaved={setEmployee}
      />
      <EditEmployeeModal
        employee={employee}
        opened={editOpen}
        onClose={editHandlers.close}
        onSaved={setEmployee}
      />
    </>
  )
}

function BackLink() {
  return (
    <Anchor component={Link} to="/employees" size="sm">
      <Group gap={4}>
        <IconArrowLeft size={14} />
        Back to employees
      </Group>
    </Anchor>
  )
}

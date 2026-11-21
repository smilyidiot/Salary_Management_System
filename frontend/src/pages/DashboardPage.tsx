// Pay analytics dashboard — the page that answers "how does the org pay people?".
// Headline KPIs, average pay by country and department, and the salary distribution,
// all normalized to USD by the backend.

import {
  Alert,
  Card,
  Center,
  Grid,
  Group,
  Loader,
  SimpleGrid,
  Table,
  Text,
  Title,
  useComputedColorScheme,
  useMantineTheme,
} from '@mantine/core'
import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { api, ApiError } from '../api/client'
import type { AnalyticsSummary, DistributionBucket, GroupStat } from '../api/types'
import { formatUsd, statusLabel } from '../lib/format'

interface DashboardData {
  summary: AnalyticsSummary
  byCountry: GroupStat[]
  byDepartment: GroupStat[]
  distribution: DistributionBucket[]
}

function StatCard({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <Card withBorder>
      <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
        {label}
      </Text>
      <Text size="xl" fw={700} mt={4}>
        {value}
      </Text>
      {hint && (
        <Text size="xs" c="dimmed" mt={2}>
          {hint}
        </Text>
      )}
    </Card>
  )
}

const usdTick = (v: number) => `$${Math.round(v / 1000)}k`

export function DashboardPage() {
  const theme = useMantineTheme()
  const scheme = useComputedColorScheme('light')
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    Promise.all([
      api.analyticsSummary(),
      api.analyticsByCountry(),
      api.analyticsByDepartment(),
      api.analyticsDistribution(),
    ])
      .then(([summary, byCountry, byDepartment, distribution]) => {
        if (active) {
          setData({ summary, byCountry, byDepartment, distribution })
          setError(null)
        }
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof ApiError ? err.message : 'Failed to load analytics')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  if (loading) {
    return (
      <Center p="xl">
        <Loader />
      </Center>
    )
  }
  if (error || !data) {
    return (
      <Alert color="red" mt="md">
        {error ?? 'No analytics available'}
      </Alert>
    )
  }

  const axisColor = scheme === 'dark' ? theme.colors.gray[5] : theme.colors.gray[7]
  const gridColor = scheme === 'dark' ? theme.colors.dark[4] : theme.colors.gray[3]
  const barColor = theme.colors.blue[6]
  const tooltipStyle = {
    backgroundColor: scheme === 'dark' ? theme.colors.dark[6] : theme.white,
    border: `1px solid ${gridColor}`,
    borderRadius: 8,
    fontSize: 13,
  }

  const countryChart = data.byCountry.map((c) => ({
    name: c.key,
    label: c.label,
    avg: Number(c.avg_salary_usd),
    median: Number(c.median_salary_usd),
  }))
  const deptChart = data.byDepartment.map((d) => ({ name: d.label, avg: Number(d.avg_salary_usd) }))
  const distChart = data.distribution.map((b) => ({ name: b.label, count: b.count }))

  const statusHint = data.summary.by_status
    .map((s) => `${statusLabel(s.status)}: ${s.count.toLocaleString()}`)
    .join(' · ')

  return (
    <>
      <Title order={2} mb="md">
        Pay analytics
      </Title>

      <SimpleGrid cols={{ base: 1, xs: 2, md: 4 }} mb="md">
        <StatCard
          label="Total headcount"
          value={data.summary.total_headcount.toLocaleString()}
          hint={statusHint}
        />
        <StatCard
          label="Total payroll (annual)"
          value={formatUsd(data.summary.total_payroll_usd)}
          hint={`${data.summary.workforce_headcount.toLocaleString()} active + on-leave`}
        />
        <StatCard label="Average salary" value={formatUsd(data.summary.average_salary_usd)} hint="USD, annualized" />
        <StatCard label="Median salary" value={formatUsd(data.summary.median_salary_usd)} hint="USD, annualized" />
      </SimpleGrid>

      <Grid>
        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card withBorder h="100%">
            <Title order={4} mb="md">
              Average salary by country (USD)
            </Title>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={countryChart} margin={{ left: 8, right: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
                <XAxis dataKey="name" tick={{ fill: axisColor, fontSize: 12 }} />
                <YAxis tickFormatter={usdTick} tick={{ fill: axisColor, fontSize: 12 }} width={48} />
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(value) => [formatUsd(Number(value)), 'Avg salary']}
                  labelFormatter={(label) =>
                    countryChart.find((c) => c.name === label)?.label ?? String(label)
                  }
                  cursor={{ fill: 'transparent' }}
                />
                <Bar dataKey="avg" fill={barColor} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 6 }}>
          <Card withBorder h="100%">
            <Title order={4} mb="md">
              Salary distribution
            </Title>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={distChart} margin={{ left: 8, right: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
                <XAxis dataKey="name" tick={{ fill: axisColor, fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={50} />
                <YAxis tick={{ fill: axisColor, fontSize: 12 }} width={40} />
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(value) => [Number(value).toLocaleString(), 'Employees']}
                  cursor={{ fill: 'transparent' }}
                />
                <Bar dataKey="count" fill={theme.colors.teal[6]} radius={[4, 4, 0, 0]}>
                  {distChart.map((_, i) => (
                    <Cell key={i} fill={theme.colors.teal[6]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Grid.Col>
      </Grid>

      <Card withBorder mt="md">
        <Title order={4} mb="md">
          Average salary by department (USD)
        </Title>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={deptChart} margin={{ left: 8, right: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
            <XAxis dataKey="name" tick={{ fill: axisColor, fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={60} />
            <YAxis tickFormatter={usdTick} tick={{ fill: axisColor, fontSize: 12 }} width={48} />
            <Tooltip
              contentStyle={tooltipStyle}
              formatter={(value) => [formatUsd(Number(value)), 'Avg salary']}
              cursor={{ fill: 'transparent' }}
            />
            <Bar dataKey="avg" fill={theme.colors.grape[6]} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card withBorder mt="md">
        <Group justify="space-between" mb="md">
          <Title order={4}>Country breakdown</Title>
        </Group>
        <Table.ScrollContainer minWidth={600}>
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Country</Table.Th>
                <Table.Th style={{ textAlign: 'right' }}>Headcount</Table.Th>
                <Table.Th style={{ textAlign: 'right' }}>Avg (USD)</Table.Th>
                <Table.Th style={{ textAlign: 'right' }}>Median (USD)</Table.Th>
                <Table.Th style={{ textAlign: 'right' }}>Total payroll (USD)</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {data.byCountry.map((c) => (
                <Table.Tr key={c.key}>
                  <Table.Td>{c.label}</Table.Td>
                  <Table.Td style={{ textAlign: 'right' }}>{c.headcount.toLocaleString()}</Table.Td>
                  <Table.Td style={{ textAlign: 'right' }}>{formatUsd(c.avg_salary_usd)}</Table.Td>
                  <Table.Td style={{ textAlign: 'right' }}>{formatUsd(c.median_salary_usd)}</Table.Td>
                  <Table.Td style={{ textAlign: 'right' }}>{formatUsd(c.total_payroll_usd)}</Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      </Card>
    </>
  )
}

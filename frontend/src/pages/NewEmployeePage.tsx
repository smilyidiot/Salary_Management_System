// Create a new employee together with their starting compensation (the backend requires an
// initial salary record, so there is never an employee without salary history).

import { Anchor, Button, Card, Grid, Group, NumberInput, Select, TextInput, Title } from '@mantine/core'
import { DateInput } from '@mantine/dates'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import { IconArrowLeft } from '@tabler/icons-react'
import dayjs from 'dayjs'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { api, ApiError } from '../api/client'
import { useReference } from '../api/ReferenceContext'
import type { CompensationReason, EmploymentStatus, PayFrequency } from '../api/types'
import {
  countryOptions,
  currencyForCountry,
  currencyOptions,
  departmentOptions,
  levelOptions,
  PAY_FREQUENCY_OPTIONS,
  STATUS_OPTIONS,
} from '../lib/options'

interface FormValues {
  full_name: string
  email: string
  country: string
  department: string
  job_title: string
  level: string
  hire_date: Date | null
  employment_status: EmploymentStatus
  base_amount: number | ''
  currency: string
  pay_frequency: PayFrequency
}

export function NewEmployeePage() {
  const navigate = useNavigate()
  const reference = useReference()
  const [submitting, setSubmitting] = useState(false)

  const form = useForm<FormValues>({
    initialValues: {
      full_name: '',
      email: '',
      country: '',
      department: '',
      job_title: '',
      level: '',
      hire_date: new Date(),
      employment_status: 'active',
      base_amount: '',
      currency: 'USD',
      pay_frequency: 'annual',
    },
    validate: {
      full_name: (v) => (v.trim() ? null : 'Required'),
      email: (v) => (/^\S+@\S+\.\S+$/.test(v) ? null : 'Enter a valid email'),
      country: (v) => (v ? null : 'Required'),
      department: (v) => (v ? null : 'Required'),
      job_title: (v) => (v.trim() ? null : 'Required'),
      level: (v) => (v ? null : 'Required'),
      base_amount: (v) => (v !== '' && Number(v) > 0 ? null : 'Enter an amount greater than 0'),
    },
  })

  // Default the currency to match the selected country.
  const handleCountry = (code: string | null) => {
    form.setFieldValue('country', code ?? '')
    const currency = currencyForCountry(reference, code)
    if (currency) form.setFieldValue('currency', currency)
  }

  const submit = form.onSubmit(async (values) => {
    setSubmitting(true)
    try {
      const hireDate = dayjs(values.hire_date).format('YYYY-MM-DD')
      const created = await api.createEmployee({
        full_name: values.full_name,
        email: values.email,
        country: values.country,
        department: values.department,
        job_title: values.job_title,
        level: values.level,
        manager_id: null,
        hire_date: hireDate,
        employment_status: values.employment_status,
        initial_compensation: {
          base_amount: String(values.base_amount),
          currency: values.currency,
          pay_frequency: values.pay_frequency,
          effective_from: hireDate,
          reason: 'hire' as CompensationReason,
        },
      })
      notifications.show({ color: 'green', message: `Created ${created.employee_code}` })
      navigate(`/employees/${created.id}`)
    } catch (err) {
      notifications.show({
        color: 'red',
        message: err instanceof ApiError ? err.message : 'Failed to create employee',
      })
    } finally {
      setSubmitting(false)
    }
  })

  return (
    <>
      <Anchor component={Link} to="/employees" size="sm">
        <Group gap={4}>
          <IconArrowLeft size={14} />
          Back to employees
        </Group>
      </Anchor>
      <Title order={2} mt="sm" mb="md">
        Add employee
      </Title>

      <form onSubmit={submit}>
        <Card withBorder mb="md">
          <Title order={4} mb="md">
            Profile
          </Title>
          <Grid>
            <Grid.Col span={{ base: 12, sm: 6 }}>
              <TextInput label="Full name" withAsterisk {...form.getInputProps('full_name')} />
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 6 }}>
              <TextInput label="Email" withAsterisk {...form.getInputProps('email')} />
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 6 }}>
              <Select
                label="Country"
                withAsterisk
                data={countryOptions(reference)}
                searchable
                {...form.getInputProps('country')}
                onChange={handleCountry}
              />
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 6 }}>
              <Select label="Department" withAsterisk data={departmentOptions(reference)} {...form.getInputProps('department')} />
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 6 }}>
              <TextInput label="Job title" withAsterisk {...form.getInputProps('job_title')} />
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 6 }}>
              <Select label="Level" withAsterisk data={levelOptions(reference)} {...form.getInputProps('level')} />
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 6 }}>
              <DateInput label="Hire date" valueFormat="YYYY-MM-DD" {...form.getInputProps('hire_date')} />
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 6 }}>
              <Select label="Status" data={STATUS_OPTIONS} {...form.getInputProps('employment_status')} />
            </Grid.Col>
          </Grid>
        </Card>

        <Card withBorder mb="md">
          <Title order={4} mb="md">
            Starting compensation
          </Title>
          <Grid>
            <Grid.Col span={{ base: 12, sm: 4 }}>
              <NumberInput
                label="Amount (per pay period)"
                withAsterisk
                min={0}
                thousandSeparator=","
                {...form.getInputProps('base_amount')}
              />
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 4 }}>
              <Select label="Currency" data={currencyOptions(reference)} {...form.getInputProps('currency')} />
            </Grid.Col>
            <Grid.Col span={{ base: 12, sm: 4 }}>
              <Select label="Pay frequency" data={PAY_FREQUENCY_OPTIONS} {...form.getInputProps('pay_frequency')} />
            </Grid.Col>
          </Grid>
        </Card>

        <Group justify="flex-end">
          <Button variant="default" type="button" onClick={() => navigate('/employees')}>
            Cancel
          </Button>
          <Button type="submit" loading={submitting}>
            Create employee
          </Button>
        </Group>
      </form>
    </>
  )
}

// Modal for editing an employee's profile fields (not their salary — that is an
// append-only history handled by the salary-change modal).

import { Button, Group, Modal, Select, Stack, TextInput } from '@mantine/core'
import { DateInput } from '@mantine/dates'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import dayjs from 'dayjs'
import { useState } from 'react'

import { api, ApiError } from '../api/client'
import { useReference } from '../api/ReferenceContext'
import type { EmployeeDetail, EmploymentStatus } from '../api/types'
import { countryOptions, departmentOptions, levelOptions, STATUS_OPTIONS } from '../lib/options'

interface FormValues {
  full_name: string
  email: string
  country: string
  department: string
  job_title: string
  level: string
  hire_date: Date | null
  employment_status: EmploymentStatus
}

export function EditEmployeeModal({
  employee,
  opened,
  onClose,
  onSaved,
}: {
  employee: EmployeeDetail
  opened: boolean
  onClose: () => void
  onSaved: (updated: EmployeeDetail) => void
}) {
  const reference = useReference()
  const [submitting, setSubmitting] = useState(false)

  const form = useForm<FormValues>({
    initialValues: {
      full_name: employee.full_name,
      email: employee.email,
      country: employee.country,
      department: employee.department,
      job_title: employee.job_title,
      level: employee.level,
      hire_date: new Date(employee.hire_date),
      employment_status: employee.employment_status,
    },
    validate: {
      full_name: (v) => (v.trim() ? null : 'Required'),
      email: (v) => (/^\S+@\S+\.\S+$/.test(v) ? null : 'Enter a valid email'),
    },
  })

  const submit = form.onSubmit(async (values) => {
    setSubmitting(true)
    try {
      const updated = await api.updateEmployee(employee.id, {
        full_name: values.full_name,
        email: values.email,
        country: values.country,
        department: values.department,
        job_title: values.job_title,
        level: values.level,
        hire_date: dayjs(values.hire_date).format('YYYY-MM-DD'),
        employment_status: values.employment_status,
      })
      notifications.show({ color: 'green', message: 'Employee updated' })
      onSaved(updated)
      onClose()
    } catch (err) {
      notifications.show({
        color: 'red',
        message: err instanceof ApiError ? err.message : 'Failed to update employee',
      })
    } finally {
      setSubmitting(false)
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title={`Edit ${employee.employee_code}`} centered>
      <form onSubmit={submit}>
        <Stack>
          <TextInput label="Full name" {...form.getInputProps('full_name')} />
          <TextInput label="Email" {...form.getInputProps('email')} />
          <Select label="Country" data={countryOptions(reference)} searchable {...form.getInputProps('country')} />
          <Select label="Department" data={departmentOptions(reference)} {...form.getInputProps('department')} />
          <TextInput label="Job title" {...form.getInputProps('job_title')} />
          <Select label="Level" data={levelOptions(reference)} {...form.getInputProps('level')} />
          <DateInput label="Hire date" valueFormat="YYYY-MM-DD" {...form.getInputProps('hire_date')} />
          <Select label="Status" data={STATUS_OPTIONS} {...form.getInputProps('employment_status')} />
          <Group justify="flex-end" mt="sm">
            <Button variant="default" onClick={onClose} type="button">
              Cancel
            </Button>
            <Button type="submit" loading={submitting}>
              Save changes
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  )
}

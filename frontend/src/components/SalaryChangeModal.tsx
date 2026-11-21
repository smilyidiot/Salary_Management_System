// Modal form for recording a salary change — appends a new effective-dated compensation
// record to an employee. Defaults currency to the employee's current currency.

import { Button, Group, Modal, NumberInput, Select, Stack } from '@mantine/core'
import { DateInput } from '@mantine/dates'
import { useForm } from '@mantine/form'
import { notifications } from '@mantine/notifications'
import dayjs from 'dayjs'
import { useState } from 'react'

import { api, ApiError } from '../api/client'
import { useReference } from '../api/ReferenceContext'
import type { CompensationReason, EmployeeDetail, PayFrequency } from '../api/types'
import { currencyOptions, PAY_FREQUENCY_OPTIONS, REASON_OPTIONS } from '../lib/options'

interface FormValues {
  base_amount: number | ''
  currency: string
  pay_frequency: PayFrequency
  effective_from: Date | null
  reason: CompensationReason
}

export function SalaryChangeModal({
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
      base_amount: '',
      currency: employee.currency ?? 'USD',
      pay_frequency: 'annual',
      effective_from: new Date(),
      reason: 'raise',
    },
    validate: {
      base_amount: (v) => (v !== '' && Number(v) > 0 ? null : 'Enter an amount greater than 0'),
      currency: (v) => (v ? null : 'Select a currency'),
      effective_from: (v) => {
        if (!v) return 'Select an effective date'
        if (dayjs(v).isBefore(dayjs(employee.hire_date))) return 'Cannot be before the hire date'
        return null
      },
    },
  })

  const submit = form.onSubmit(async (values) => {
    setSubmitting(true)
    try {
      const updated = await api.addCompensation(employee.id, {
        base_amount: String(values.base_amount),
        currency: values.currency,
        pay_frequency: values.pay_frequency,
        effective_from: dayjs(values.effective_from).format('YYYY-MM-DD'),
        reason: values.reason,
      })
      notifications.show({ color: 'green', message: 'Salary change recorded' })
      onSaved(updated)
      form.reset()
      onClose()
    } catch (err) {
      notifications.show({
        color: 'red',
        message: err instanceof ApiError ? err.message : 'Failed to record change',
      })
    } finally {
      setSubmitting(false)
    }
  })

  return (
    <Modal opened={opened} onClose={onClose} title="Record salary change" centered>
      <form onSubmit={submit}>
        <Stack>
          <NumberInput
            label="Amount (per pay period)"
            placeholder="0"
            min={0}
            thousandSeparator=","
            {...form.getInputProps('base_amount')}
          />
          <Select
            label="Currency"
            data={currencyOptions(reference)}
            {...form.getInputProps('currency')}
          />
          <Select
            label="Pay frequency"
            data={PAY_FREQUENCY_OPTIONS}
            {...form.getInputProps('pay_frequency')}
          />
          <DateInput
            label="Effective from"
            valueFormat="YYYY-MM-DD"
            {...form.getInputProps('effective_from')}
          />
          <Select label="Reason" data={REASON_OPTIONS} {...form.getInputProps('reason')} />
          <Group justify="flex-end" mt="sm">
            <Button variant="default" onClick={onClose} type="button">
              Cancel
            </Button>
            <Button type="submit" loading={submitting}>
              Record change
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  )
}

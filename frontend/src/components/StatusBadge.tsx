// Colored badge for an employment status, reused in the list and detail views.

import { Badge } from '@mantine/core'

import type { EmploymentStatus } from '../api/types'
import { statusLabel } from '../lib/format'

const COLORS: Record<EmploymentStatus, string> = {
  active: 'green',
  on_leave: 'yellow',
  terminated: 'gray',
}

export function StatusBadge({ status }: { status: EmploymentStatus }) {
  return (
    <Badge color={COLORS[status]} variant="light">
      {statusLabel(status)}
    </Badge>
  )
}

// App shell: header + sidebar navigation wrapping the routed page content.

import { AppShell, Group, NavLink, Text, ThemeIcon } from '@mantine/core'
import { IconChartBar, IconUsers, IconWallet } from '@tabler/icons-react'
import type { ReactNode } from 'react'
import { NavLink as RouterNavLink, useLocation } from 'react-router-dom'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: IconChartBar, end: true },
  { to: '/employees', label: 'Employees', icon: IconUsers, end: false },
]

export function Layout({ children }: { children: ReactNode }) {
  const location = useLocation()

  return (
    <AppShell header={{ height: 56 }} navbar={{ width: 240, breakpoint: 'sm' }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" gap="sm">
          <ThemeIcon variant="light" size="md" radius="md">
            <IconWallet size={18} />
          </ThemeIcon>
          <Text fw={700}>Salary Management</Text>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="sm">
        {NAV_ITEMS.map((item) => {
          const active = item.end
            ? location.pathname === item.to
            : location.pathname.startsWith(item.to)
          return (
            <NavLink
              key={item.to}
              component={RouterNavLink}
              to={item.to}
              label={item.label}
              leftSection={<item.icon size={18} />}
              active={active}
            />
          )
        })}
      </AppShell.Navbar>

      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  )
}

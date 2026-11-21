// Application routes, wrapped in the shared layout.
//
// Pages are lazy-loaded so the initial download only contains the shell plus the first
// route's code. Heavy, page-specific dependencies (Recharts on the dashboard, the date/form
// libraries on the employee forms) load on demand rather than up front.

import { Center, Loader } from '@mantine/core'
import { Suspense, lazy } from 'react'
import { Route, Routes } from 'react-router-dom'

import { Layout } from './components/Layout'

const DashboardPage = lazy(() =>
  import('./pages/DashboardPage').then((m) => ({ default: m.DashboardPage })),
)
const EmployeesPage = lazy(() =>
  import('./pages/EmployeesPage').then((m) => ({ default: m.EmployeesPage })),
)
const EmployeeDetailPage = lazy(() =>
  import('./pages/EmployeeDetailPage').then((m) => ({ default: m.EmployeeDetailPage })),
)
const NewEmployeePage = lazy(() =>
  import('./pages/NewEmployeePage').then((m) => ({ default: m.NewEmployeePage })),
)

export default function App() {
  return (
    <Layout>
      <Suspense
        fallback={
          <Center p="xl">
            <Loader />
          </Center>
        }
      >
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/employees" element={<EmployeesPage />} />
          <Route path="/employees/new" element={<NewEmployeePage />} />
          <Route path="/employees/:id" element={<EmployeeDetailPage />} />
        </Routes>
      </Suspense>
    </Layout>
  )
}

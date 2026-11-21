// Application routes, wrapped in the shared layout.

import { Route, Routes } from 'react-router-dom'

import { Layout } from './components/Layout'
import { DashboardPage } from './pages/DashboardPage'
import { EmployeeDetailPage } from './pages/EmployeeDetailPage'
import { EmployeesPage } from './pages/EmployeesPage'
import { NewEmployeePage } from './pages/NewEmployeePage'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/employees" element={<EmployeesPage />} />
        <Route path="/employees/new" element={<NewEmployeePage />} />
        <Route path="/employees/:id" element={<EmployeeDetailPage />} />
      </Routes>
    </Layout>
  )
}

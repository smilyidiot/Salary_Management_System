// Loads the backend's reference data (countries, departments, levels, enums) once and
// shares it with filter bars and forms, so the UI and API agree on valid option values.

import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

import { api } from './client'
import type { ReferenceData } from './types'

const ReferenceContext = createContext<ReferenceData | null>(null)

export function ReferenceProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<ReferenceData | null>(null)

  useEffect(() => {
    api.reference().then(setData).catch(() => setData(null))
  }, [])

  return <ReferenceContext.Provider value={data}>{children}</ReferenceContext.Provider>
}

export function useReference(): ReferenceData | null {
  return useContext(ReferenceContext)
}

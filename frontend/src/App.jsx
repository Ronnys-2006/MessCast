import React, { useEffect, useState } from 'react'
import { BarChart3, CalendarDays, ChefHat, LayoutDashboard, Leaf, SlidersHorizontal, WifiOff } from 'lucide-react'
import { api, subscribe } from './api'
import { Badge, Skeleton } from './components/ui'
import Dashboard from './pages/Dashboard'
import Simulator from './pages/Simulator'
import Models from './pages/Models'
import Waste from './pages/Waste'
import Plan from './pages/Plan'

const PAGES = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, title: 'Tomorrow at a glance', C: Dashboard },
  { id: 'simulator', label: 'What-if simulator', icon: SlidersHorizontal, title: 'What-if simulator', C: Simulator },
  { id: 'models', label: 'Model comparison', icon: BarChart3, title: 'Model comparison', C: Models },
  { id: 'waste', label: 'Waste savings', icon: Leaf, title: 'Waste savings', C: Waste },
  { id: 'plan', label: 'Weekly plan', icon: CalendarDays, title: 'Weekly cooking plan', C: Plan },
]

export default function App() {
  const [page, setPage] = useState('dashboard')
  const [opts, setOpts] = useState(null)
  const [offline, setOffline] = useState(false)

  useEffect(() => subscribe(setOffline), [])
  useEffect(() => { api.options().then(setOpts) }, [])

  const current = PAGES.find((p) => p.id === page)
  const Page = current.C

  return (
    <div className="min-h-screen lg:flex">
      <aside className="hidden w-64 shrink-0 flex-col bg-slate-900 p-5 text-slate-300 lg:flex">
        <div className="mb-8 flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 text-white shadow-lg shadow-emerald-900/40">
            <ChefHat size={22} />
          </span>
          <div>
            <p className="text-lg font-bold leading-tight text-white">MessCast</p>
            <p className="text-[11px] uppercase tracking-widest text-slate-500">cook what's needed</p>
          </div>
        </div>
        <nav className="space-y-1">
          {PAGES.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setPage(id)}
              className={`flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition ${
                page === id ? 'bg-emerald-500/15 text-emerald-300 ring-1 ring-emerald-500/30' : 'hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>
        <div className="mt-auto rounded-2xl bg-slate-800/70 p-4 text-xs leading-relaxed text-slate-400">
          <p className="mb-1 font-semibold text-slate-200">Predict. Cook. Save.</p>
          Aligned with SDG 12 (responsible consumption) and SDG 2 (zero hunger).
        </div>
      </aside>

      <div className="flex min-h-screen min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 border-b border-slate-200/70 bg-slate-50/85 backdrop-blur">
          <div className="flex items-center justify-between gap-4 px-5 py-4 lg:px-8">
            <div>
              <h1 className="text-xl font-bold tracking-tight text-slate-900">{current.title}</h1>
              <p className="text-xs text-slate-500">Meal demand forecasting to reduce mess food waste</p>
            </div>
            <div className="flex items-center gap-2">
              {opts && <Badge tone="emerald">Model: {opts.model}</Badge>}
            </div>
          </div>
          <nav className="flex gap-1 overflow-x-auto px-4 pb-2 lg:hidden">
            {PAGES.map(({ id, label }) => (
              <button
                key={id}
                onClick={() => setPage(id)}
                className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-semibold ${
                  page === id ? 'bg-slate-900 text-white' : 'bg-white text-slate-600 ring-1 ring-slate-200'
                }`}
              >
                {label}
              </button>
            ))}
          </nav>
        </header>

        {offline && (
          <div className="mx-5 mt-4 flex items-center gap-2 rounded-xl bg-amber-50 px-4 py-2.5 text-sm text-amber-800 ring-1 ring-amber-200 lg:mx-8">
            <WifiOff size={16} />
            Backend not reachable. Showing embedded demo results (start it with <code className="rounded bg-amber-100 px-1">uvicorn api.main:app --reload</code>).
          </div>
        )}

        <main className="flex-1 space-y-6 px-5 py-6 lg:px-8">
          {opts ? <Page opts={opts} /> : <div className="grid gap-4 sm:grid-cols-3"><Skeleton /><Skeleton /><Skeleton /></div>}
        </main>

        <footer className="border-t border-slate-200 px-5 py-4 text-center text-xs text-slate-500 lg:px-8">
          MessCast · Meal demand forecasting to reduce mess food waste
        </footer>
      </div>
    </div>
  )
}

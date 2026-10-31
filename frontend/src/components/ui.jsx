import React from 'react'
import { MEAL_STYLE } from '../utils'

export function Card({ title, subtitle, right, children, className = '' }) {
  return (
    <section className={`rounded-2xl bg-white p-5 shadow-soft ring-1 ring-slate-200/70 fade-in ${className}`}>
      {(title || right) && (
        <header className="mb-4 flex items-start justify-between gap-3">
          <div>
            {title && <h3 className="text-sm font-semibold text-slate-900">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
          </div>
          {right}
        </header>
      )}
      {children}
    </section>
  )
}

const TONES = {
  emerald: 'from-emerald-500 to-teal-500',
  amber: 'from-amber-400 to-orange-500',
  indigo: 'from-indigo-500 to-violet-500',
  rose: 'from-rose-500 to-pink-500',
  sky: 'from-sky-500 to-cyan-500',
}

export function Kpi({ label, value, unit, hint, icon: Icon, tone = 'emerald' }) {
  return (
    <div className="relative overflow-hidden rounded-2xl bg-white p-5 shadow-soft ring-1 ring-slate-200/70 fade-in">
      <div className={`absolute -right-6 -top-6 h-24 w-24 rounded-full bg-gradient-to-br ${TONES[tone]} opacity-10`} />
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
        {Icon && (
          <span className={`grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br ${TONES[tone]} text-white shadow`}>
            <Icon size={18} />
          </span>
        )}
      </div>
      <p className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
        {value}
        {unit && <span className="ml-1 text-base font-medium text-slate-400">{unit}</span>}
      </p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  )
}

export function MealTabs({ value, onChange, meals = ['Breakfast', 'Lunch', 'Dinner'] }) {
  return (
    <div className="inline-flex rounded-xl bg-slate-100 p-1">
      {meals.map((m) => (
        <button
          key={m}
          onClick={() => onChange(m)}
          className={`rounded-lg px-3.5 py-1.5 text-sm font-medium transition ${
            value === m ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          <span className="mr-1">{MEAL_STYLE[m].emoji}</span>
          {m}
        </button>
      ))}
    </div>
  )
}

export function Tabs({ value, onChange, items }) {
  return (
    <div className="inline-flex rounded-xl bg-slate-100 p-1">
      {items.map((m) => (
        <button
          key={m}
          onClick={() => onChange(m)}
          className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
            value === m ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'
          }`}
        >
          {m}
        </button>
      ))}
    </div>
  )
}

export function Toggle({ label, checked, onChange, hint }) {
  return (
    <label className="flex cursor-pointer items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 transition hover:border-emerald-300">
      <span>
        <span className="block text-sm font-medium text-slate-800">{label}</span>
        {hint && <span className="block text-xs text-slate-500">{hint}</span>}
      </span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-11 shrink-0 rounded-full transition ${checked ? 'bg-emerald-500' : 'bg-slate-300'}`}
      >
        <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all ${checked ? 'left-[22px]' : 'left-0.5'}`} />
      </button>
    </label>
  )
}

export function Field({ label, children, right }) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between">
        <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</label>
        {right && <span className="text-sm font-semibold text-slate-800">{right}</span>}
      </div>
      {children}
    </div>
  )
}

export const inputCls =
  'w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-emerald-400 focus:ring-4 focus:ring-emerald-100'

export function Skeleton({ className = 'h-24' }) {
  return <div className={`animate-pulse rounded-2xl bg-slate-200/70 ${className}`} />
}

export function Badge({ children, tone = 'slate' }) {
  const t = {
    slate: 'bg-slate-100 text-slate-600',
    emerald: 'bg-emerald-100 text-emerald-700',
    amber: 'bg-amber-100 text-amber-700',
    rose: 'bg-rose-100 text-rose-700',
  }[tone]
  return <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${t}`}>{children}</span>
}

export const chartTip = {
  contentStyle: { borderRadius: 12, border: '1px solid #e2e8f0', boxShadow: '0 8px 24px -12px rgba(15,23,42,.25)', fontSize: 12 },
}

import React, { useEffect, useMemo, useState } from 'react'
import { Download } from 'lucide-react'
import { api } from '../api'
import { Card, Field, inputCls, Skeleton } from '../components/ui'
import { addDays, downloadCsv, fmtDate, MEAL_STYLE, num } from '../utils'

export default function Plan({ opts }) {
  const [start, setStart] = useState(addDays(opts.history_end, 1))
  const [menus, setMenus] = useState(() =>
    Object.fromEntries(opts.meals.map((m) => [m, Array.from({ length: 7 }, (_, i) => opts.menu_by_meal[m][i % opts.menu_by_meal[m].length])])),
  )
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let live = true
    Promise.all(opts.meals.map((m) => api.week({ start_date: start, meal: m, menu_item: menus[m][0], menu_items: menus[m] })))
      .then((r) => { if (live) { setData(Object.fromEntries(opts.meals.map((m, i) => [m, r[i]]))); setError('') } })
      .catch((e) => live && setError(e.message))
    return () => { live = false }
  }, [start, menus])

  const setMenu = (meal, i, v) => setMenus((p) => ({ ...p, [meal]: p[meal].map((x, j) => (j === i ? v : x)) }))

  const totals = useMemo(() => {
    if (!data) return []
    return Array.from({ length: 7 }, (_, i) => ({
      cook: opts.meals.reduce((s, m) => s + data[m][i].suggested_cook_plates, 0),
      saved: opts.meals.reduce((s, m) => s + data[m][i].expected_saving_kg, 0),
    }))
  }, [data])

  const exportCsv = () => {
    const rows = []
    opts.meals.forEach((m) => data[m].forEach((d) => rows.push({
      date: d.date, weekday: d.weekday, meal: m, menu_item: d.menu_item, predicted_plates: d.predicted_plates,
      suggested_cook_plates: d.suggested_cook_plates, expected_saving_kg: d.expected_saving_kg,
    })))
    rows.sort((a, b) => a.date.localeCompare(b.date))
    downloadCsv(`messcast_plan_${start}.csv`, rows)
  }

  return (
    <Card title="Weekly cooking plan" subtitle="Pick the menu for each meal; quantities update automatically."
      right={
        <div className="flex items-end gap-3">
          <Field label="Week starting"><input type="date" value={start} onChange={(e) => e.target.value && setStart(e.target.value)} className={inputCls} /></Field>
          <button onClick={exportCsv} disabled={!data}
            className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow transition hover:bg-slate-700 disabled:opacity-40">
            <Download size={16} /> CSV
          </button>
        </div>
      }>
      {error && <p className="mb-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
      {!data ? <Skeleton className="h-96" /> : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                <th className="py-2 pr-3">Day</th>
                {opts.meals.map((m) => <th key={m} className="px-2">{MEAL_STYLE[m].emoji} {m}</th>)}
                <th className="pl-3 text-right">Day total</th>
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: 7 }, (_, i) => (
                <tr key={i} className="border-b border-slate-100 align-top">
                  <td className="whitespace-nowrap py-3 pr-3 font-semibold text-slate-900">{fmtDate(addDays(start, i))}</td>
                  {opts.meals.map((m) => {
                    const r = data[m][i]
                    return (
                      <td key={m} className="px-2 py-2.5">
                        <select value={menus[m][i]} onChange={(e) => setMenu(m, i, e.target.value)}
                          className="mb-1 w-full rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs outline-none focus:border-emerald-400">
                          {opts.menu_by_meal[m].map((x) => <option key={x}>{x}</option>)}
                        </select>
                        <p className="text-xs text-slate-500">predicted {num(r.predicted_plates)}</p>
                        <p className="text-base font-bold text-slate-900">cook {num(r.suggested_cook_plates)}</p>
                      </td>
                    )
                  })}
                  <td className="pl-3 text-right">
                    <p className="text-base font-bold text-slate-900">{num(totals[i].cook)}</p>
                    <p className="text-xs text-emerald-600">saves {num(totals[i].saved, 1)} kg</p>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  )
}

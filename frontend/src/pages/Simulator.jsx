import React, { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { CloudRain, Sparkles, Thermometer } from 'lucide-react'
import { api } from '../api'
import { Card, chartTip, Field, inputCls, MealTabs, Toggle } from '../components/ui'
import { addDays, MEAL_STYLE, num } from '../utils'

export default function Simulator({ opts }) {
  const [f, setF] = useState({
    date: addDays(opts.history_end, 5), meal: 'Lunch', menu_item: opts.menu_by_meal.Lunch[0],
    is_holiday: 0, is_exam_period: 0, is_vacation: 0, is_event: 0, temperature_c: 25, rain_mm: 0,
  })
  const [res, setRes] = useState(null)
  const [week, setWeek] = useState(null)
  const [error, setError] = useState('')
  const set = (patch) => setF((p) => ({ ...p, ...patch }))

  useEffect(() => {
    let live = true
    const t = setTimeout(() => {
      const { date, ...cond } = f
      api.predict(f).then((r) => { if (live) { setRes(r); setError('') } }).catch((e) => live && setError(e.message))
      api.week({ ...cond, start_date: date }).then((w) => live && setWeek(w)).catch(() => {})
    }, 300)
    return () => { live = false; clearTimeout(t) }
  }, [f])

  const fixed = opts.fixed_plates[f.meal]
  const maxBar = res ? Math.max(fixed, res.suggested_cook_plates, res.predicted_plates) * 1.08 : 1
  const diff = res ? res.suggested_cook_plates - fixed : 0
  const color = MEAL_STYLE[f.meal].color

  return (
    <div className="grid gap-6 xl:grid-cols-5">
      <Card className="xl:col-span-2" title="Conditions" subtitle="Change anything. The prediction updates live.">
        <div className="space-y-4">
          <MealTabs value={f.meal} onChange={(m) => set({ meal: m, menu_item: opts.menu_by_meal[m][0] })} />
          <div className="grid grid-cols-2 gap-3">
            <Field label="Date"><input type="date" value={f.date} onChange={(e) => e.target.value && set({ date: e.target.value })} className={inputCls} /></Field>
            <Field label="Menu">
              <select value={f.menu_item} onChange={(e) => set({ menu_item: e.target.value })} className={inputCls}>
                {opts.menu_by_meal[f.meal].map((m) => <option key={m} value={m}>{m}{opts.special.includes(m) ? ' ★' : ''}</option>)}
              </select>
            </Field>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            <Toggle label="Holiday" checked={!!f.is_holiday} onChange={(v) => set({ is_holiday: +v })} />
            <Toggle label="Exam period" checked={!!f.is_exam_period} onChange={(v) => set({ is_exam_period: +v })} />
            <Toggle label="Vacation" checked={!!f.is_vacation} onChange={(v) => set({ is_vacation: +v })} />
            <Toggle label="Special event" checked={!!f.is_event} onChange={(v) => set({ is_event: +v })} />
          </div>
          <Field label="Temperature" right={<span className="inline-flex items-center gap-1"><Thermometer size={14} />{f.temperature_c} °C</span>}>
            <input type="range" min="15" max="35" step="0.5" value={f.temperature_c} onChange={(e) => set({ temperature_c: +e.target.value })} />
          </Field>
          <Field label="Rain" right={<span className="inline-flex items-center gap-1"><CloudRain size={14} />{f.rain_mm} mm</span>}>
            <input type="range" min="0" max="30" step="0.5" value={f.rain_mm} onChange={(e) => set({ rain_mm: +e.target.value })} />
          </Field>
          <p className="text-xs text-slate-500">★ special dish. Lags (yesterday, last week) come from history; dates beyond it use earlier forecasts.</p>
        </div>
      </Card>

      <div className="space-y-6 xl:col-span-3">
        <Card>
          {error && <p className="mb-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
          {!res ? <div className="h-40 animate-pulse rounded-xl bg-slate-100" /> : (
            <>
              <div className="flex flex-wrap items-end justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Predicted plates</p>
                  <p className="text-6xl font-extrabold tracking-tight" style={{ color }}>{num(res.predicted_plates)}</p>
                </div>
                <div className="grid grid-cols-2 gap-3 text-right">
                  <div className="rounded-xl bg-slate-900 px-4 py-2.5 text-white">
                    <p className="text-[11px] uppercase tracking-wide text-slate-400">Cook</p>
                    <p className="text-2xl font-bold">{num(res.suggested_cook_plates)}</p>
                  </div>
                  <div className="rounded-xl bg-emerald-500 px-4 py-2.5 text-white">
                    <p className="text-[11px] uppercase tracking-wide text-emerald-100">Food saved</p>
                    <p className="text-2xl font-bold">{num(res.expected_saving_kg, 1)} kg</p>
                  </div>
                </div>
              </div>

              <div className="mt-6 space-y-2.5">
                {[['Usual (fixed) cooking', fixed, '#f97316'], ['Predicted demand', res.predicted_plates, color], ['Suggested cooking (+5%)', res.suggested_cook_plates, '#0f172a']].map(([l, v, c]) => (
                  <div key={l}>
                    <div className="mb-1 flex justify-between text-xs text-slate-500"><span>{l}</span><span className="font-semibold text-slate-800">{num(v)}</span></div>
                    <div className="h-2.5 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full transition-all duration-500" style={{ width: `${(v / maxBar) * 100}%`, background: c }} /></div>
                  </div>
                ))}
              </div>

              <div className="mt-5 flex items-start gap-2 rounded-xl bg-slate-50 p-3.5 text-sm text-slate-700 ring-1 ring-slate-200">
                <Sparkles size={16} className="mt-0.5 shrink-0 text-emerald-600" />
                {diff <= 0
                  ? <span>Cook <b>{num(-diff)} fewer plates</b> than the usual {fixed}. Expected saving about <b>{num(res.expected_saving_kg, 1)} kg</b> of food.</span>
                  : <span>Demand is high: cook <b>{num(diff)} more plates</b> than the usual {fixed} to avoid a shortage.</span>}
              </div>
            </>
          )}
        </Card>

        <Card title="Next 7 days with these conditions" subtitle="Same menu and conditions applied to each day">
          {!week ? <div className="h-48 animate-pulse rounded-xl bg-slate-100" /> : (
            <ResponsiveContainer width="100%" height={210}>
              <BarChart data={week.map((d) => ({ day: d.weekday, plates: d.predicted_plates }))} margin={{ left: -16, top: 6 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="day" tickLine={false} axisLine={false} fontSize={12} />
                <YAxis tickLine={false} axisLine={false} fontSize={12} />
                <Tooltip {...chartTip} cursor={{ fill: '#f1f5f9' }} />
                <Bar dataKey="plates" radius={[8, 8, 0, 0]}>
                  {week.map((_, i) => <Cell key={i} fill={color} fillOpacity={i === 0 ? 1 : 0.55} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </Card>
      </div>
    </div>
  )
}

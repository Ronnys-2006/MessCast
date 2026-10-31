import React, { useEffect, useState } from 'react'
import { Area, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Flame, Leaf, Scale, Utensils } from 'lucide-react'
import { api } from '../api'
import { Card, chartTip, Field, inputCls, Kpi, MealTabs, Skeleton } from '../components/ui'
import { addDays, fmtDate, MEAL_STYLE, num } from '../utils'

export default function Dashboard({ opts }) {
  const [meal, setMeal] = useState('Lunch')
  const [start, setStart] = useState(addDays(opts.history_end, 1))
  const [menus, setMenus] = useState({
    Breakfast: opts.menu_by_meal.Breakfast[0], Lunch: opts.menu_by_meal.Lunch[0], Dinner: opts.menu_by_meal.Dinner[0],
  })
  const [week, setWeek] = useState(null)
  const [allMeals, setAllMeals] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let live = true
    setError('')
    api.week({ start_date: start, meal, menu_item: menus[meal] })
      .then((w) => live && setWeek(w))
      .catch((e) => live && setError(e.message))
    return () => { live = false }
  }, [start, meal, menus[meal]])

  useEffect(() => {
    let live = true
    Promise.all(opts.meals.map((m) => api.predict({ date: start, meal: m, menu_item: menus[m] })))
      .then((r) => live && setAllMeals(r))
      .catch(() => {})
    return () => { live = false }
  }, [start, menus.Breakfast, menus.Lunch, menus.Dinner])

  const fixed = opts.fixed_plates[meal]
  const first = week && week[0]
  const chart = week && week.map((d) => ({
    day: d.weekday, Predicted: d.predicted_plates, 'Suggested cooking': d.suggested_cook_plates, 'Fixed cooking': fixed,
  }))
  const delta = first ? first.suggested_cook_plates - fixed : 0

  return (
    <>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <MealTabs value={meal} onChange={setMeal} />
        <div className="flex flex-wrap gap-3">
          <Field label="Planning date">
            <input type="date" value={start} onChange={(e) => e.target.value && setStart(e.target.value)} className={inputCls} />
          </Field>
          <Field label={`${meal} menu`}>
            <select value={menus[meal]} onChange={(e) => setMenus({ ...menus, [meal]: e.target.value })} className={inputCls}>
              {opts.menu_by_meal[meal].map((m) => <option key={m}>{m}</option>)}
            </select>
          </Field>
        </div>
      </div>

      {error && <p className="rounded-xl bg-rose-50 px-4 py-2 text-sm text-rose-700 ring-1 ring-rose-200">{error}</p>}

      {!first ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"><Skeleton /><Skeleton /><Skeleton /><Skeleton /></div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <Kpi label="Predicted plates" value={num(first.predicted_plates)} unit="plates" icon={Utensils} tone="indigo"
               hint={`${meal} on ${fmtDate(start)}`} />
          <Kpi label="Suggested cooking" value={num(first.suggested_cook_plates)} unit="plates" icon={Flame} tone="amber"
               hint={delta <= 0 ? `${num(-delta)} fewer than the usual ${fixed} (incl. 5% buffer)` : `${num(delta)} MORE than the usual ${fixed}`} />
          <Kpi label="Food saved" value={num(first.expected_saving_kg, 1)} unit="kg" icon={Leaf} tone="emerald"
               hint="vs cooking the fixed amount" />
          <Kpi label="Fixed cooking today" value={num(fixed)} unit="plates" icon={Scale} tone="sky" hint="what the mess cooks now" />
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2" title="7-day forecast" subtitle={`${meal} · from ${fmtDate(start)} · each day feeds the next (recursive forecast)`}>
          {!chart ? <Skeleton className="h-72" /> : (
            <ResponsiveContainer width="100%" height={300}>
              <ComposedChart data={chart} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
                <defs>
                  <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={MEAL_STYLE[meal].color} stopOpacity={0.35} />
                    <stop offset="100%" stopColor={MEAL_STYLE[meal].color} stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis dataKey="day" tickLine={false} axisLine={false} fontSize={12} />
                <YAxis tickLine={false} axisLine={false} fontSize={12} domain={['dataMin - 80', 'dataMax + 80']} />
                <Tooltip {...chartTip} />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                <Area type="monotone" dataKey="Predicted" stroke={MEAL_STYLE[meal].color} strokeWidth={3} fill="url(#g)" />
                <Line type="monotone" dataKey="Suggested cooking" stroke="#0f172a" strokeWidth={2} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="Fixed cooking" stroke="#f97316" strokeDasharray="6 4" strokeWidth={2} dot={false} />
              </ComposedChart>
            </ResponsiveContainer>
          )}
        </Card>

        <Card title={`All meals · ${fmtDate(start)}`} subtitle="Suggested plates to cook">
          <div className="space-y-3">
            {opts.meals.map((m, i) => {
              const r = allMeals && allMeals[i]
              return (
                <div key={m} className={`rounded-xl p-3.5 ring-1 ${MEAL_STYLE[m].soft}`}>
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold">{MEAL_STYLE[m].emoji} {m}</p>
                    <p className="text-xs opacity-80">{menus[m]}</p>
                  </div>
                  {r ? (
                    <div className="mt-1.5 flex items-end justify-between">
                      <p className="text-2xl font-bold">{num(r.suggested_cook_plates)}<span className="ml-1 text-xs font-medium opacity-70">plates</span></p>
                      <p className="text-xs opacity-80">predicted {num(r.predicted_plates)} · saves {num(r.expected_saving_kg, 1)} kg</p>
                    </div>
                  ) : <div className="mt-2 h-7 animate-pulse rounded bg-white/60" />}
                </div>
              )
            })}
          </div>
        </Card>
      </div>
    </>
  )
}

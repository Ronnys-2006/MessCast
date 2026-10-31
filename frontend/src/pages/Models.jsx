import React, { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Trophy } from 'lucide-react'
import { api } from '../api'
import { Badge, Card, chartTip, MealTabs, Skeleton, Tabs } from '../components/ui'
import { MEAL_STYLE, num } from '../utils'

const COLORS = {
  Baseline: '#94a3b8', 'Naive (yesterday)': '#cbd5e1', 'Linear Regression': '#f59e0b', 'Random Forest': '#10b981',
  'Gradient Boosting': '#0ea5e9', XGBoost: '#6366f1', 'Deep MLP': '#e11d48',
}

export default function Models() {
  const [metrics, setMetrics] = useState(null)
  const [detail, setDetail] = useState(null)
  const [rows, setRows] = useState(null)
  const [metric, setMetric] = useState('MAE')
  const [meal, setMeal] = useState('Lunch')

  useEffect(() => {
    api.metrics().then(setMetrics)
    api.metricsDetailed().then(setDetail)
    api.testPredictions().then(setRows)
  }, [])

  if (!metrics) return <Skeleton className="h-96" />
  const best = metrics.best_model
  const names = Object.keys(metrics).filter((k) => k !== 'best_model')
  const base = metrics.Baseline.MAE
  const bars = names.map((n) => ({ name: n, value: metrics[n][metric] }))
  const series = rows && rows.filter((r) => r.meal === meal).map((r) => ({
    date: r.date.slice(5), Actual: +r.actual, [best]: +r[best], Baseline: +r.Baseline,
  }))

  return (
    <>
      <div className="grid gap-6 xl:grid-cols-5">
        <Card className="xl:col-span-3" title="Test-set results" subtitle="Lower is better · last ~15% of days, never used for tuning">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
                  <th className="py-2 pr-3">Model</th><th className="px-3">MAE</th><th className="px-3">RMSE</th><th className="px-3">MAPE %</th><th className="pl-3">vs baseline</th>
                </tr>
              </thead>
              <tbody>
                {names.map((n) => {
                  const m = metrics[n]
                  const gain = (1 - m.MAE / base) * 100
                  return (
                    <tr key={n} className={`border-b border-slate-100 ${n === best ? 'bg-emerald-50/60' : ''}`}>
                      <td className="py-2.5 pr-3 font-medium text-slate-900">
                        <span className="mr-2 inline-block h-2.5 w-2.5 rounded-full" style={{ background: COLORS[n] || '#64748b' }} />
                        {n} {n === best && <Trophy size={14} className="ml-1 inline text-amber-500" />}
                      </td>
                      <td className="px-3 tabular-nums">{num(m.MAE, 1)}</td>
                      <td className="px-3 tabular-nums">{num(m.RMSE, 1)}</td>
                      <td className="px-3 tabular-nums">{num(m.MAPE, 2)}</td>
                      <td className="pl-3">{n === 'Baseline' ? <Badge>reference</Badge> : <Badge tone={gain > 0 ? 'emerald' : 'rose'}>{gain > 0 ? '−' : '+'}{num(Math.abs(gain), 0)}% error</Badge>}</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {detail && (
            <p className="mt-3 text-xs text-slate-500">
              Best model chosen by cross-validation on train+val ({detail.n_trainval_rows} rows), then scored once on {detail.n_test_rows} test rows.
              Differences between the top models are small and within noise.
            </p>
          )}
        </Card>

        <Card className="xl:col-span-2" title="Compare" right={<Tabs value={metric} onChange={setMetric} items={['MAE', 'RMSE', 'MAPE']} />}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={bars} layout="vertical" margin={{ left: 24, right: 24 }}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
              <XAxis type="number" tickLine={false} axisLine={false} fontSize={12} />
              <YAxis type="category" dataKey="name" width={110} tickLine={false} axisLine={false} fontSize={11} />
              <Tooltip {...chartTip} cursor={{ fill: '#f1f5f9' }} formatter={(v) => num(v, 2)} />
              <Bar dataKey="value" radius={[0, 8, 8, 0]} label={{ position: 'right', fontSize: 11, formatter: (v) => num(v, 1) }}>
                {bars.map((b) => <Cell key={b.name} fill={COLORS[b.name] || '#64748b'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card title="Actual vs predicted" subtitle={`Test period · ${best} vs baseline`} right={<MealTabs value={meal} onChange={setMeal} />}>
        {!series ? <Skeleton className="h-72" /> : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={series} margin={{ left: -12, right: 8 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="date" tickLine={false} axisLine={false} fontSize={11} />
              <YAxis tickLine={false} axisLine={false} fontSize={12} domain={['auto', 'auto']} />
              <Tooltip {...chartTip} />
              <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="Actual" stroke="#0f172a" strokeWidth={2.5} dot={{ r: 3 }} />
              <Line type="monotone" dataKey={best} stroke={MEAL_STYLE[meal].color} strokeWidth={2.5} strokeDasharray="5 3" dot={false} />
              <Line type="monotone" dataKey="Baseline" stroke="#94a3b8" strokeWidth={1.8} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </Card>
    </>
  )
}

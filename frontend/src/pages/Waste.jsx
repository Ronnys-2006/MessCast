import React, { useEffect, useState } from 'react'
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { AlertTriangle, Leaf, Percent, Utensils } from 'lucide-react'
import { api } from '../api'
import { Card, chartTip, Kpi, Skeleton } from '../components/ui'
import { num } from '../utils'

export default function Waste() {
  const [w, setW] = useState(null)
  useEffect(() => { api.waste().then(setW) }, [])
  if (!w) return <Skeleton className="h-96" />

  const perMeal = Object.entries(w.per_meal).map(([meal, v]) => ({
    meal, 'Fixed cooking': Math.round(v.fixed.leftover_kg), 'Forecast cooking': Math.round(v.forecast.leftover_kg),
  }))
  let cum = 0
  const saved = w.daily.map((d) => {
    cum += d.fixed_leftover_kg - d.forecast_leftover_kg
    return { date: d.date.slice(5), 'Cumulative kg saved': Math.round(cum) }
  })

  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi label="Leftover reduced" value={num(w.leftover_reduction_pct, 0)} unit="%" icon={Percent} tone="emerald" hint={`over ${w.period}`} />
        <Kpi label="Food saved" value={num(w.kg_saved, 0)} unit="kg" icon={Leaf} tone="indigo" hint={`${num(w.fixed.leftover_kg, 0)} → ${num(w.forecast.leftover_kg, 0)} kg leftover`} />
        <Kpi label="Plates not wasted" value={num(w.fixed.leftover_plates - w.forecast.leftover_plates)} unit="plates" icon={Utensils} tone="amber" hint="cooked but never eaten, avoided" />
        <Kpi label="Shortage plates" value={`${num(w.fixed.shortage_plates)} → ${num(w.forecast.shortage_plates)}`} icon={AlertTriangle} tone="rose" hint={`${w.fixed.shortage_days} → ${w.forecast.shortage_days} short meals`} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card title="Leftover food by meal" subtitle="Fixed cooking (today) vs forecast × 1.05 · test period, kg">
          <ResponsiveContainer width="100%" height={290}>
            <BarChart data={perMeal} margin={{ left: -8 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="meal" tickLine={false} axisLine={false} fontSize={12} />
              <YAxis tickLine={false} axisLine={false} fontSize={12} />
              <Tooltip {...chartTip} cursor={{ fill: '#f1f5f9' }} />
              <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
              <Bar dataKey="Fixed cooking" fill="#f97316" radius={[8, 8, 0, 0]} />
              <Bar dataKey="Forecast cooking" fill="#10b981" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        <Card title="Food saved over time" subtitle="Cumulative kg of leftover avoided">
          <ResponsiveContainer width="100%" height={290}>
            <AreaChart data={saved} margin={{ left: -8 }}>
              <defs>
                <linearGradient id="sv" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#10b981" stopOpacity={0.4} /><stop offset="100%" stopColor="#10b981" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
              <XAxis dataKey="date" tickLine={false} axisLine={false} fontSize={11} />
              <YAxis tickLine={false} axisLine={false} fontSize={12} />
              <Tooltip {...chartTip} />
              <Area type="monotone" dataKey="Cumulative kg saved" stroke="#059669" strokeWidth={3} fill="url(#sv)" />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </div>

      <Card title="Why a 5% buffer?" subtitle="Analysis on the same test period. A bigger buffer prevents shortages but brings the waste back.">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead><tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
              <th className="py-2">Buffer</th><th>Leftover (kg)</th><th>Shortage (plates)</th><th>Short meals</th></tr></thead>
            <tbody>
              {w.buffer_sensitivity.map((b) => (
                <tr key={b.buffer} className={`border-b border-slate-100 ${Math.abs(b.buffer - w.buffer) < 1e-6 ? 'bg-emerald-50/70 font-semibold' : ''}`}>
                  <td className="py-2">× {b.buffer.toFixed(2)}{Math.abs(b.buffer - w.buffer) < 1e-6 ? '  (used)' : ''}</td>
                  <td className="tabular-nums">{num(b.leftover_kg, 0)}</td><td className="tabular-nums">{num(b.shortage_plates)}</td><td>{b.shortage_days}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  )
}

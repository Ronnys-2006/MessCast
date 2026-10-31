export const MEAL_STYLE = {
  Breakfast: { color: '#f59e0b', soft: 'bg-amber-50 text-amber-700 ring-amber-200', emoji: '🌅' },
  Lunch: { color: '#10b981', soft: 'bg-emerald-50 text-emerald-700 ring-emerald-200', emoji: '☀️' },
  Dinner: { color: '#6366f1', soft: 'bg-indigo-50 text-indigo-700 ring-indigo-200', emoji: '🌙' },
}

export const iso = (d) => d.toISOString().slice(0, 10)

export function addDays(isoDate, n) {
  const d = new Date(isoDate + 'T00:00:00Z')
  d.setUTCDate(d.getUTCDate() + n)
  return iso(d)
}

export const fmtDate = (isoDate) =>
  new Date(isoDate + 'T00:00:00Z').toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', timeZone: 'UTC' })

export const num = (n, d = 0) => Number(n).toLocaleString('en-IN', { maximumFractionDigits: d, minimumFractionDigits: d })

export function downloadCsv(filename, rows) {
  if (!rows.length) return
  const cols = Object.keys(rows[0])
  const text = [cols.join(','), ...rows.map((r) => cols.map((c) => JSON.stringify(r[c] ?? '')).join(','))].join('\n')
  const url = URL.createObjectURL(new Blob([text], { type: 'text/csv' }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

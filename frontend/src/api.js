// All backend calls live here. If the API is not running, we fall back to the embedded demo data
// (real project results + a rough stand-in model) so the UI never breaks during a demo.
import { MOCK, mockPredict, mockWeek } from './mockData'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
let offline = false
const subs = new Set()

export function subscribe(fn) {
  subs.add(fn)
  fn(offline)
  return () => subs.delete(fn)
}
function setOffline(v) {
  if (v !== offline) { offline = v; subs.forEach((f) => f(v)) }
}

async function call(path, body) {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 4000)
  try {
    const res = await fetch(BASE + path, {
      method: body ? 'POST' : 'GET',
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) {
      const msg = (data.problems && data.problems.join('; ')) || data.detail || data.error || 'Request failed'
      const err = new Error(typeof msg === 'string' ? msg : JSON.stringify(msg))
      err.userError = true
      throw err
    }
    setOffline(false)
    return data
  } finally {
    clearTimeout(timer)
  }
}

async function withFallback(real, mock) {
  try { return await real() } catch (e) {
    if (e.userError) throw e
    setOffline(true)
    return mock()
  }
}

export const api = {
  options: () => withFallback(() => call('/options'), () => MOCK.options),
  predict: (b) => withFallback(() => call('/predict', b), () => mockPredict(b)),
  week: (b) => withFallback(() => call('/forecast-week', b), () => mockWeek(b)),
  metrics: () => withFallback(() => call('/metrics'), () => MOCK.metrics),
  metricsDetailed: () => withFallback(() => call('/metrics-detailed'), () => MOCK.metricsDetailed),
  waste: () => withFallback(() => call('/waste'), () => MOCK.waste),
  testPredictions: () => withFallback(() => call('/test-predictions'), () => MOCK.testPredictions),
}

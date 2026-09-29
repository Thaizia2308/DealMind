import { useState } from 'react'
import { api } from '../lib/api'
import { ErrorBox } from './Answer'

function MemoryPill({ status }) {
  if (!status) return <p className="text-xs text-mute">Checking Hindsight...</p>
  if (!status.configured) {
    return (
      <div className="rounded-md bg-warnsoft px-3 py-2 text-xs text-warn">
        <p className="font-semibold">Hindsight not configured</p>
        <p className="mt-0.5">Add credentials to .env to enable memory.</p>
      </div>
    )
  }
  if (!status.reachable) {
    return (
      <div className="rounded-md bg-badsoft px-3 py-2 text-xs text-bad" title={status.error || ''}>
        <p className="font-semibold">Hindsight unreachable</p>
        <p className="mt-0.5 break-words">{(status.error || '').slice(0, 110)}</p>
      </div>
    )
  }
  return (
    <div className="rounded-md bg-oksoft px-3 py-2 text-xs text-ok">
      <p className="font-semibold">Hindsight connected ({status.mode})</p>
      {status.server_version && <p className="mt-0.5">Server version {status.server_version}</p>}
    </div>
  )
}

export default function Sidebar({ customers, selectedId, onSelect, onCreated, memStatus }) {
  const [adding, setAdding] = useState(false)
  const [form, setForm] = useState({ name: '', company: '', industry: '' })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function create(e) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const c = await api.createCustomer(form)
      setForm({ name: '', company: '', industry: '' })
      setAdding(false)
      await onCreated(c.id)
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  async function demo() {
    setBusy(true)
    setError(null)
    try {
      const c = await api.demoCustomer()
      await onCreated(c.id)
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  return (
    <aside className="flex w-full shrink-0 flex-col gap-4 border-b border-line bg-white p-5 md:h-full md:w-72 md:border-b-0 md:border-r">
      <div>
        <h1 className="font-serif text-2xl font-semibold tracking-tight">DealMind</h1>
        <p className="text-xs text-mute">The sales assistant that remembers every customer.</p>
      </div>

      <div className="flex flex-col gap-2">
        <button className="btn-primary" onClick={demo} disabled={busy}>Start judge demo (Rahul)</button>
        <button className="btn-quiet" onClick={() => setAdding((v) => !v)}>{adding ? 'Cancel' : 'New customer'}</button>
      </div>

      {adding && (
        <form onSubmit={create} className="flex flex-col gap-2">
          <div><label className="label" htmlFor="cn">Name</label><input id="cn" required className="field" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} maxLength={200} /></div>
          <div><label className="label" htmlFor="cc">Company</label><input id="cc" required className="field" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} maxLength={200} /></div>
          <div><label className="label" htmlFor="ci">Industry</label><input id="ci" className="field" value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} maxLength={200} /></div>
          <button className="btn-primary" disabled={busy}>{busy ? 'Creating...' : 'Create customer'}</button>
        </form>
      )}
      <ErrorBox error={error} />

      <nav aria-label="Customers" className="min-h-0 flex-1 overflow-y-auto">
        {customers.length === 0 ? (
          <p className="text-sm text-mute">No customers yet. Start the judge demo or create one.</p>
        ) : (
          <ul className="flex flex-col">
            {customers.map((c) => (
              <li key={c.id}>
                <button
                  onClick={() => onSelect(c.id)}
                  aria-current={c.id === selectedId ? 'true' : undefined}
                  className={`w-full border-l-2 px-3 py-2 text-left text-sm ${c.id === selectedId ? 'border-mem bg-memsoft/60' : 'border-transparent hover:bg-fog'}`}
                >
                  <span className="block font-semibold">{c.name}</span>
                  <span className="block text-xs text-mute">{c.company}{c.industry ? `, ${c.industry}` : ''} - {c.interaction_count} {c.interaction_count === 1 ? 'interaction' : 'interactions'}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </nav>

      <MemoryPill status={memStatus} />
    </aside>
  )
}

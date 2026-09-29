import { useState } from 'react'
import { api } from '../lib/api'
import { ErrorBox } from './Answer'

const KINDS = [
  ['note', 'Note'],
  ['call', 'Call'],
  ['meeting', 'Meeting'],
  ['email', 'Email'],
  ['demo', 'Product demo'],
]

function fmt(iso) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export function Composer({ customer, onAdded }) {
  const [text, setText] = useState('')
  const [kind, setKind] = useState('note')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  async function submit(e) {
    e.preventDefault()
    if (!text.trim()) return
    setBusy(true)
    setError(null)
    try {
      await api.addInteraction(customer.id, { content: text.trim(), kind })
      setText('')
      await onAdded()
    } catch (err) {
      setError(err)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-2">
      <label className="label" htmlFor="note">What happened with {customer.name}?</label>
      <textarea id="note" className="field min-h-[76px]" value={text} onChange={(e) => setText(e.target.value)} placeholder="e.g. Asked about SOC 2 compliance" maxLength={5000} />
      <div className="flex items-center gap-2">
        <select aria-label="Interaction type" className="field !w-auto" value={kind} onChange={(e) => setKind(e.target.value)}>
          {KINDS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        <button className="btn-primary" disabled={busy || !text.trim()}>
          {busy ? 'Saving to memory...' : 'Save to memory'}
        </button>
      </div>
      <ErrorBox error={error} />
    </form>
  )
}

export function Timeline({ interactions, onChanged }) {
  const [retrying, setRetrying] = useState(null)
  async function retry(id) {
    setRetrying(id)
    try { await api.retryInteraction(id) } finally { setRetrying(null); await onChanged() }
  }

  if (interactions.length === 0) {
    return <p className="text-sm text-mute">No interactions yet. Everything you record here is sent to Hindsight so DealMind can remember it.</p>
  }
  return (
    <ol className="flex flex-col">
      {interactions.map((i) => (
        <li key={i.id} className="border-t border-line py-3 first:border-t-0 first:pt-0">
          <div className="flex items-center justify-between gap-2 text-xs text-mute">
            <span className="font-semibold capitalize text-ink">{i.kind}</span>
            <time dateTime={i.occurred_at}>{fmt(i.occurred_at)}</time>
          </div>
          <p className="mt-1 text-sm">{i.content}</p>
          <div className="mt-1.5 text-xs">
            {i.retained ? (
              <span className="rounded bg-oksoft px-1.5 py-0.5 font-semibold text-ok">Stored in Hindsight</span>
            ) : (
              <span className="inline-flex flex-wrap items-center gap-2">
                <span className="rounded bg-warnsoft px-1.5 py-0.5 font-semibold text-warn">Not stored in Hindsight</span>
                <button className="font-semibold text-mem underline" disabled={retrying === i.id} onClick={() => retry(i.id)}>
                  {retrying === i.id ? 'Retrying...' : 'Retry'}
                </button>
                {i.retain_error && <span className="text-mute" title={i.retain_error}>{i.retain_error.slice(0, 80)}{i.retain_error.length > 80 ? '...' : ''}</span>}
              </span>
            )}
          </div>
        </li>
      ))}
    </ol>
  )
}

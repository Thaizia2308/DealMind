import { useState } from 'react'
import { api } from '../lib/api'
import { ErrorBox } from './Answer'

export default function DemoGuide({ script, interactions, customer, onAdded }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const have = new Set(interactions.map((i) => i.content))
  const isDone = (s) => have.has(s.content)
  const done = script.steps.filter(isDone).length
  const next = script.steps.find((s) => !isDone(s))

  async function addNext() {
    setBusy(true)
    setError(null)
    try {
      await api.addInteraction(customer.id, next)
      await onAdded()
    } catch (e) {
      setError(e)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="rounded-lg border border-mem/30 bg-memsoft/50 p-4 text-sm">
      <h3 className="font-bold">Judge demo</h3>
      <p className="mt-1 text-mute">
        Step 1: on the Meeting prep tab, click <b>Show without memory</b>. Step 2: add the five interactions below.
        Step 3: click <b>Prepare me for {customer.name}&apos;s meeting</b> and compare.
      </p>
      <ol className="mt-3 space-y-1">
        {script.steps.map((s, idx) => (
          <li key={idx} className={isDone(s) ? 'text-ok' : s === next ? 'font-semibold' : 'text-mute'}>
            {isDone(s) ? 'Done: ' : s === next ? 'Next: ' : 'Later: '}
            {s.content}
          </li>
        ))}
      </ol>
      {next ? (
        <button className="btn-primary mt-3" disabled={busy} onClick={addNext}>
          {busy ? 'Saving to memory...' : 'Add next interaction'}
        </button>
      ) : (
        <p className="mt-3 font-semibold text-ok">All five interactions are in memory. Now ask: &ldquo;{script.question}&rdquo;</p>
      )}
      <div className="mt-2"><ErrorBox error={error} /></div>
    </div>
  )
}

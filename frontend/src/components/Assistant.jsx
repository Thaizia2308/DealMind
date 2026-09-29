import { useState } from 'react'
import { api } from '../lib/api'
import { Answer, ErrorBox, Spinner } from './Answer'

const TABS = [
  { id: 'prepare', label: 'Meeting prep' },
  { id: 'ask', label: 'Ask about customer' },
  { id: 'followup', label: 'Follow-up' },
]

export default function Assistant({ customer, memStatus }) {
  const [tab, setTab] = useState('prepare')
  const [results, setResults] = useState({})
  const [busy, setBusy] = useState('')
  const [error, setError] = useState(null)
  const [goal, setGoal] = useState('')
  const [question, setQuestion] = useState('')
  const [channel, setChannel] = useState('email')
  const [tone, setTone] = useState('professional')
  const [instructions, setInstructions] = useState('')

  const first = customer.name.split(' ')[0]
  const noMemory = memStatus && !memStatus.configured

  async function run(key, label, fn) {
    setBusy(label)
    setError(null)
    try {
      const r = await fn()
      setResults((prev) => ({ ...prev, [key]: r }))
    } catch (e) {
      setError(e)
    } finally {
      setBusy('')
    }
  }

  const prepare = (useMemory) =>
    run(useMemory ? 'prep-mem' : 'prep-nomem', useMemory ? 'Hindsight is recalling what it knows and writing the briefing... this can take 10-30 seconds.' : 'Preparing generic checklist...', () =>
      api.prepare(customer.id, { use_memory: useMemory, meeting_goal: goal }),
    )

  const suggestions = [
    `What is ${first} most worried about?`,
    `What has ${first} asked us for so far?`,
    `Which objections should I expect from ${first}?`,
  ]

  return (
    <div className="flex flex-col gap-4">
      <div role="tablist" className="flex gap-1 border-b border-line">
        {TABS.map((t) => (
          <button
            key={t.id}
            role="tab"
            aria-selected={tab === t.id}
            onClick={() => { setTab(t.id); setError(null) }}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-semibold ${tab === t.id ? 'border-mem text-mem' : 'border-transparent text-mute hover:text-ink'}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {noMemory && (
        <p className="rounded-md bg-warnsoft px-4 py-2.5 text-sm text-warn">
          Hindsight credentials are missing, so memory-based answers are unavailable. Only the generic
          (no-memory) checklist will work until you configure Hindsight.
        </p>
      )}

      {tab === 'prepare' && (
        <div className="flex flex-col gap-4">
          <div>
            <label className="label" htmlFor="goal">Meeting goal (optional)</label>
            <input id="goal" className="field" value={goal} onChange={(e) => setGoal(e.target.value)} placeholder="e.g. Agree on the evaluation plan" maxLength={500} />
          </div>
          <div className="flex flex-wrap gap-2">
            <button className="btn-primary" disabled={!!busy || noMemory} onClick={() => prepare(true)}>
              Prepare me for {first}&apos;s meeting
            </button>
            <button className="btn-quiet" disabled={!!busy} onClick={() => prepare(false)} title="Shows what an assistant with no memory would give you">
              Show without memory
            </button>
          </div>
          {busy && <Spinner label={busy} />}
          <ErrorBox error={error} />
          <div className={`grid gap-4 ${results['prep-nomem'] && results['prep-mem'] ? 'xl:grid-cols-2' : ''}`}>
            {results['prep-nomem'] && <Answer title="Without memory" result={results['prep-nomem']} />}
            {results['prep-mem'] && <Answer title="With memory" result={results['prep-mem']} />}
          </div>
        </div>
      )}

      {tab === 'ask' && (
        <div className="flex flex-col gap-4">
          <div>
            <label className="label" htmlFor="q">Your question</label>
            <textarea id="q" className="field min-h-[72px]" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder={`Ask anything about ${first}...`} maxLength={2000} />
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestions.map((s) => (
              <button key={s} className="btn-quiet !py-1 text-xs" onClick={() => setQuestion(s)}>{s}</button>
            ))}
          </div>
          <div>
            <button className="btn-primary" disabled={!!busy || !question.trim() || noMemory} onClick={() => run('ask', 'Asking Hindsight...', () => api.ask(customer.id, question))}>
              Ask
            </button>
          </div>
          {busy && <Spinner label={busy} />}
          <ErrorBox error={error} />
          {results.ask && <Answer title="Answer" result={results.ask} />}
        </div>
      )}

      {tab === 'followup' && (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label" htmlFor="ch">Format</label>
              <select id="ch" className="field" value={channel} onChange={(e) => setChannel(e.target.value)}>
                <option value="email">Email</option>
                <option value="message">Short message</option>
              </select>
            </div>
            <div>
              <label className="label" htmlFor="tone">Tone</label>
              <select id="tone" className="field" value={tone} onChange={(e) => setTone(e.target.value)}>
                <option value="professional">Professional</option>
                <option value="friendly">Friendly</option>
                <option value="concise">Concise</option>
              </select>
            </div>
          </div>
          <div>
            <label className="label" htmlFor="ins">Extra instructions (optional)</label>
            <input id="ins" className="field" value={instructions} onChange={(e) => setInstructions(e.target.value)} placeholder="e.g. Offer a call on Thursday" maxLength={500} />
          </div>
          <div>
            <button className="btn-primary" disabled={!!busy || noMemory} onClick={() => run('followup', 'Hindsight is drafting the follow-up... this can take 10-30 seconds.', () => api.followup(customer.id, { channel, tone, instructions }))}>
              Write follow-up
            </button>
          </div>
          {busy && <Spinner label={busy} />}
          <ErrorBox error={error} />
          {results.followup && <Answer title="Follow-up draft" result={results.followup} />}
        </div>
      )}
    </div>
  )
}

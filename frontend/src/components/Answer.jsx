import ReactMarkdown from 'react-markdown'

export function Spinner({ label }) {
  return (
    <div className="flex items-center gap-3 py-6 text-sm text-mute" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-line border-t-mem" />
      {label}
    </div>
  )
}

export function ErrorBox({ error }) {
  if (!error) return null
  const notConfigured = error.code === 'hindsight_not_configured'
  return (
    <div className="rounded-md border border-bad/30 bg-badsoft px-4 py-3 text-sm text-bad" role="alert">
      <p className="font-semibold">{notConfigured ? 'Hindsight is not set up yet' : 'Something went wrong'}</p>
      <p className="mt-1 whitespace-pre-wrap break-words">{error.message}</p>
      {notConfigured && (
        <p className="mt-1">Add your Hindsight credentials to the .env file and restart the backend (see README).</p>
      )}
    </div>
  )
}

export function SourceBadge({ source }) {
  if (source === 'hindsight') {
    return (
      <span className="rounded bg-memsoft px-2 py-0.5 text-xs font-semibold text-mem">
        Built from Hindsight memory
      </span>
    )
  }
  return (
    <span className="rounded bg-warnsoft px-2 py-0.5 text-xs font-semibold text-warn">
      Generic template - no memory used
    </span>
  )
}

export function Answer({ result, title }) {
  const generic = result.source !== 'hindsight'
  return (
    <section
      className={`rounded-lg border bg-white ${generic ? 'border-warn/30' : 'border-mem/30'}`}
      aria-label={title}
    >
      <header className={`flex flex-wrap items-center justify-between gap-2 border-b px-5 py-2.5 ${generic ? 'border-warn/20 bg-warnsoft/40' : 'border-mem/20 bg-memsoft/50'}`}>
        <h3 className="text-sm font-bold">{title}</h3>
        <SourceBadge source={result.source} />
      </header>
      <div className="brief px-5 pb-4 pt-1">
        <ReactMarkdown>{result.answer}</ReactMarkdown>
      </div>
      {result.memories?.length > 0 && (
        <details className="border-t border-line px-5 py-3 text-sm">
          <summary className="cursor-pointer font-semibold text-mem">
            Memories Hindsight recalled ({result.memories.length})
          </summary>
          <ul className="mt-2 space-y-1.5 text-mute">
            {result.memories.map((m, i) => (
              <li key={i} className="border-l-2 border-mem/40 pl-3">
                {m.text}
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  )
}

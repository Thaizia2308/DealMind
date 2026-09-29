import { useCallback, useEffect, useState } from 'react'
import { api, API_URL } from './lib/api'
import Sidebar from './components/Sidebar'
import Assistant from './components/Assistant'
import DemoGuide from './components/DemoGuide'
import { Composer, Timeline } from './components/Timeline'
import { ErrorBox } from './components/Answer'

export default function App() {
  const [customers, setCustomers] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [interactions, setInteractions] = useState([])
  const [memStatus, setMemStatus] = useState(null)
  const [script, setScript] = useState(null)
  const [loading, setLoading] = useState(true)
  const [backendError, setBackendError] = useState(null)

  const refreshCustomers = useCallback(async () => {
    const list = await api.listCustomers()
    setCustomers(list)
    return list
  }, [])

  const refreshInteractions = useCallback(async (id) => {
    if (id == null) return setInteractions([])
    setInteractions(await api.listInteractions(id))
  }, [])

  const refreshAll = useCallback(async () => {
    await refreshCustomers()
    await refreshInteractions(selectedId)
  }, [refreshCustomers, refreshInteractions, selectedId])

  useEffect(() => {
    (async () => {
      try {
        await api.health()
        const list = await refreshCustomers()
        if (list.length) setSelectedId(list[0].id)
        api.memoryStatus().then(setMemStatus).catch(() => {})
        api.demoScript().then(setScript).catch(() => {})
      } catch (e) {
        setBackendError(e)
      } finally {
        setLoading(false)
      }
    })()
  }, [refreshCustomers])

  useEffect(() => {
    refreshInteractions(selectedId).catch((e) => setBackendError(e))
  }, [selectedId, refreshInteractions])

  const customer = customers.find((c) => c.id === selectedId)

  async function onCreated(id) {
    await refreshCustomers()
    setSelectedId(id)
  }

  async function remove() {
    if (!customer || !window.confirm(`Delete ${customer.name} and their memory in Hindsight?`)) return
    await api.deleteCustomer(customer.id)
    const list = await refreshCustomers()
    setSelectedId(list.length ? list[0].id : null)
  }

  return (
    <div className="flex min-h-full flex-col md:h-full md:flex-row">
      <Sidebar customers={customers} selectedId={selectedId} onSelect={setSelectedId} onCreated={onCreated} memStatus={memStatus} />

      <main className="min-w-0 flex-1 overflow-y-auto p-5 md:p-8">
        {loading ? (
          <p className="text-sm text-mute" role="status">Loading...</p>
        ) : backendError ? (
          <div className="max-w-xl">
            <h2 className="mb-3 text-lg font-bold">DealMind cannot reach its backend</h2>
            <ErrorBox error={backendError} />
            <p className="mt-3 text-sm text-mute">
              Backend URL in use: <code>{API_URL || '(same origin, i.e. the address of this page)'}</code>. Start the
              backend (see README) and reload this page.
            </p>
          </div>
        ) : !customer ? (
          <div className="max-w-lg">
            <h2 className="font-serif text-3xl font-semibold">Walk into every meeting knowing the customer.</h2>
            <p className="mt-3 text-mute">
              DealMind stores what each customer says in Hindsight, then uses that memory to prepare your meetings and write your follow-ups.
              Click <b>Start judge demo</b> on the left, or create your own customer.
            </p>
          </div>
        ) : (
          <div className="mx-auto max-w-6xl">
            <header className="mb-6 flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="font-serif text-3xl font-semibold leading-tight">{customer.name}</h2>
                <p className="text-sm text-mute">{customer.company}{customer.industry ? ` - ${customer.industry}` : ''}</p>
                {customer.bank_id && <p className="mt-0.5 text-xs text-mute">Hindsight memory bank: <code>{customer.bank_id}</code></p>}
              </div>
              <button className="btn-quiet !py-1 text-xs" onClick={remove}>Delete customer</button>
            </header>

            <div className="grid gap-8 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)]">
              <div className="flex flex-col gap-6">
                {customer.is_demo && script && (
                  <DemoGuide script={script} interactions={interactions} customer={customer} onAdded={refreshAll} />
                )}
                <Composer customer={customer} onAdded={refreshAll} />
                <div>
                  <h3 className="mb-3 text-sm font-bold">Memory timeline</h3>
                  <Timeline interactions={interactions} onChanged={refreshAll} />
                </div>
              </div>
              <Assistant key={customer.id} customer={customer} memStatus={memStatus} />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

import { useEffect, useState } from 'react'
import apiClient from '../api/client'

function SystemStatus() {
  const [status, setStatus] = useState(null)
  const [checking, setChecking] = useState(false)

  function loadStatus(deep) {
    setChecking(true)
    apiClient.get('/system/status', { params: { deep_check: deep } })
      .then((res) => setStatus(res.data))
      .finally(() => setChecking(false))
  }

  useEffect(() => {
    loadStatus(false)
  }, [])

  if (!status) return <p className="font-mono text-sm">Loading...</p>

  const entries = Object.entries(status).filter(([key]) => key !== 'overall')

  return (
    <div>
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <h2 className="font-display font-extrabold text-4xl">System</h2>
        <button
          onClick={() => loadStatus(true)}
          disabled={checking}
          className="bg-cardinal text-white font-display font-semibold text-sm px-5 py-2 rounded-full hover:-translate-y-0.5 transition-transform disabled:opacity-50"
        >
          {checking ? 'Checking...' : 'Run Deep Check (tests Gmail)'}
        </button>
      </div>

      <div className="bg-white rounded-2xl p-6 mb-6 flex items-center gap-3">
        <span className={status.overall === 'all_systems_configured' ? 'status-pulse' : 'w-3 h-3 rounded-full bg-cardinal flex-shrink-0'}></span>
        <p className="font-display font-semibold text-lg">
          {status.overall === 'all_systems_configured' ? 'All systems configured' : 'Some systems need attention'}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {entries.map(([key, value]) => (
          <div key={key} className="bg-white rounded-2xl p-4 flex items-center justify-between">
            <span className="font-mono text-sm capitalize">{key.replace(/_/g, ' ')}</span>
            <span
              className={
                value === 'configured' || value === 'connected_successfully'
                  ? 'font-display font-semibold text-xs px-3 py-1 rounded-full bg-mustard text-ink'
                  : 'font-display font-semibold text-xs px-3 py-1 rounded-full bg-cardinal text-white'
              }
            >
              {value}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default SystemStatus

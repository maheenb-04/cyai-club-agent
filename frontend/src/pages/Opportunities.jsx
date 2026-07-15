import { useEffect, useState } from 'react'
import apiClient from '../api/client'

const statusColor = {
  valid: 'bg-green-600',
  dead: 'bg-cardinal',
  unchecked: 'bg-mustard',
}

function Opportunities() {
  const [opportunities, setOpportunities] = useState([])
  const [category, setCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    apiClient
      .get('/opportunities/', { params: category ? { category } : {} })
      .then((res) => setOpportunities(res.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [category])

  const categories = ['scholarship', 'internship', 'job', 'ctf', 'bootcamp', 'fellowship']

  return (
    <div>
      <h2 className="font-display font-bold text-4xl mb-1">Opportunities</h2>
      <p className="font-mono text-sm text-ink-soft mb-6">
        {opportunities.length} active {category || 'items'}
      </p>

      <div className="flex flex-wrap gap-2 mb-6">
        <button
          onClick={() => setCategory('')}
          className={`font-display font-semibold text-sm px-4 py-2 rounded ${
            category === '' ? 'bg-ink text-paper' : 'bg-cream text-ink'
          }`}
        >
          All
        </button>
        {categories.map((c) => (
          <button
            key={c}
            onClick={() => setCategory(c)}
            className={`font-display font-semibold text-sm px-4 py-2 rounded capitalize ${
              category === c ? 'bg-ink text-paper' : 'bg-cream text-ink'
            }`}
          >
            {c}
          </button>
        ))}
      </div>

      {loading && <p className="font-mono text-sm">Loading...</p>}
      {error && <p className="font-mono text-sm text-cardinal">Error: {error}</p>}

      <div className="space-y-3">
        {opportunities.map((opp) => (
          <div
            key={opp.id}
            className="bg-white rounded-lg shadow-sm border-l-4 border-cardinal p-4 flex items-start justify-between gap-4"
          >
            <div className="flex-1">
              <h3 className="font-display font-semibold text-lg">{opp.title}</h3>
              <p className="text-sm text-ink-soft">{opp.organization}</p>
              <p className="font-mono text-xs text-ink-soft mt-2">
                {opp.category.toUpperCase()} - {opp.deadline || 'Rolling'} - {opp.source_type}
              </p>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0">
              <span className={`w-2.5 h-2.5 rounded-full ${statusColor[opp.link_status] || 'bg-gray-300'}`} title={opp.link_status}></span>
              <a href={opp.url} target="_blank" rel="noreferrer" className="font-display font-semibold text-sm text-cardinal hover:underline">View</a>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Opportunities

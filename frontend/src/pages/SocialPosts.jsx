import { useEffect, useState } from 'react'
import apiClient from '../api/client'

function SocialPosts() {
  const [posts, setPosts] = useState([])
  const [opportunities, setOpportunities] = useState([])
  const [events, setEvents] = useState([])
  const [platform, setPlatform] = useState('circlein')
  const [sourceType, setSourceType] = useState('opportunity')
  const [sourceId, setSourceId] = useState('')
  const [generating, setGenerating] = useState(false)

  function loadPosts() {
    apiClient.get('/social-posts/').then((res) => setPosts(res.data))
  }

  useEffect(() => {
    loadPosts()
    apiClient.get('/opportunities/').then((res) => setOpportunities(res.data))
    apiClient.get('/events/').then((res) => setEvents(res.data))
  }, [])

  function handleGenerate() {
    if (!sourceId) return
    setGenerating(true)
    const params = { platform }
    if (sourceType === 'opportunity') params.opportunity_id = sourceId
    else params.event_id = sourceId

    apiClient.post('/social-posts/generate', null, { params }).then(() => {
      setSourceId('')
      loadPosts()
    }).finally(() => setGenerating(false))
  }

  function handleDelete(id) {
    if (!confirm('Delete this post?')) return
    apiClient.delete('/social-posts/' + id).then(() => loadPosts())
  }

  function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
    alert('Copied to clipboard')
  }

  return (
    <div>
      <h2 className="font-display font-extrabold text-4xl mb-6">Social Posts</h2>

      <div className="bg-white rounded-2xl p-5 mb-6 space-y-3">
        <div className="flex gap-3 flex-wrap">
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="border border-periwinkle rounded-full px-4 py-2 font-body text-sm"
          >
            <option value="circlein">CircleIn</option>
            <option value="instagram">Instagram</option>
          </select>
          <select
            value={sourceType}
            onChange={(e) => { setSourceType(e.target.value); setSourceId('') }}
            className="border border-periwinkle rounded-full px-4 py-2 font-body text-sm"
          >
            <option value="opportunity">From Opportunity</option>
            <option value="event">From Event</option>
          </select>
          <select
            value={sourceId}
            onChange={(e) => setSourceId(e.target.value)}
            className="border border-periwinkle rounded-full px-4 py-2 font-body text-sm flex-1 min-w-[200px]"
          >
            <option value="">Select...</option>
            {sourceType === 'opportunity' && opportunities.map((o) => (
              <option key={o.id} value={o.id}>{o.title}</option>
            ))}
            {sourceType === 'event' && events.map((ev) => (
              <option key={ev.id} value={ev.id}>{ev.title}</option>
            ))}
          </select>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating || !sourceId}
          className="bg-cardinal text-white font-display font-semibold text-sm px-5 py-2 rounded-full hover:-translate-y-0.5 transition-transform disabled:opacity-50"
        >
          {generating ? 'Generating...' : 'Generate Post'}
        </button>
      </div>

      <div className="space-y-3">
        {posts.map((p) => (
          <div key={p.id} className="bg-white rounded-2xl p-5">
            <div className="flex items-center justify-between mb-2">
              <span className="font-display font-semibold text-xs px-3 py-1 rounded-full bg-periwinkle text-ink capitalize">
                {p.platform}
              </span>
              <button onClick={() => handleDelete(p.id)} className="font-display font-semibold text-xs text-cardinal">
                Delete
              </button>
            </div>
            {p.platform === 'circlein' && (
              <div>
                <p className="font-body text-sm whitespace-pre-wrap mb-3" dangerouslySetInnerHTML={{ __html: p.content }} />
                <button
                  onClick={() => copyToClipboard(p.content.replace(/<[^>]*>/g, ''))}
                  className="bg-mustard text-ink font-display font-semibold text-xs px-4 py-2 rounded-full"
                >
                  Copy Text
                </button>
              </div>
            )}
            {p.platform === 'instagram' && (
              <div>
                <p className="font-body text-sm mb-2">{p.caption}</p>
                <p className="font-mono text-xs text-periwinkle mb-3">{p.hashtags}</p>
                <button
                  onClick={() => copyToClipboard(p.caption + '\n\n' + p.hashtags)}
                  className="bg-mustard text-ink font-display font-semibold text-xs px-4 py-2 rounded-full"
                >
                  Copy Caption
                </button>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default SocialPosts

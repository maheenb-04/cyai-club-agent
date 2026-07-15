import { useEffect, useState } from 'react'
import apiClient from '../api/client'

function Newsletters() {
  const [newsletters, setNewsletters] = useState([])
  const [monthLabel, setMonthLabel] = useState('')
  const [generating, setGenerating] = useState(false)
  const [selected, setSelected] = useState(null)
  const [editSubject, setEditSubject] = useState('')
  const [editHtml, setEditHtml] = useState('')
  const [confirmSend, setConfirmSend] = useState(false)

  function loadNewsletters() {
    apiClient.get('/newsletters/').then((res) => setNewsletters(res.data))
  }

  useEffect(() => {
    loadNewsletters()
  }, [])

  function handleGenerate() {
    if (!monthLabel.trim()) return
    setGenerating(true)
    apiClient
      .post('/newsletters/generate', null, { params: { month_label: monthLabel } })
      .then(() => {
        setMonthLabel('')
        loadNewsletters()
      })
      .finally(() => setGenerating(false))
  }

  function openNewsletter(n) {
    setSelected(n)
    setEditSubject(n.subject || '')
    setEditHtml(n.html_content || '')
    setConfirmSend(false)
  }

  function saveChanges() {
    apiClient
      .patch('/newsletters/' + selected.id, { subject: editSubject, html_content: editHtml })
      .then((res) => {
        setSelected(res.data)
        loadNewsletters()
      })
  }

  function sendNewsletter() {
    apiClient.post('/newsletters/' + selected.id + '/send').then((res) => {
      alert('Sent to ' + res.data.sent + ' of ' + res.data.recipients_attempted + ' members')
      setSelected(null)
      loadNewsletters()
    })
  }

  return (
    <div>
      <h2 className="font-display font-extrabold text-4xl mb-6">Newsletters</h2>

      <div className="bg-white rounded-2xl p-5 mb-6 flex flex-col md:flex-row gap-3 md:items-center">
        <input
          type="text"
          value={monthLabel}
          onChange={(e) => setMonthLabel(e.target.value)}
          placeholder="e.g. September"
          className="border border-periwinkle rounded-full px-4 py-2 font-body text-sm flex-1"
        />
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="bg-cardinal text-white font-display font-semibold text-sm px-5 py-2 rounded-full hover:-translate-y-0.5 transition-transform disabled:opacity-50"
        >
          {generating ? 'Generating...' : 'Generate Newsletter'}
        </button>
      </div>

      {!selected && (
        <div className="space-y-3">
          {newsletters.map((n) => (
            <button
              key={n.id}
              onClick={() => openNewsletter(n)}
              className="w-full text-left bg-white rounded-2xl p-5 hover:-translate-y-0.5 transition-transform flex items-center justify-between gap-4"
            >
              <div>
                <h3 className="font-display font-semibold text-lg">{n.subject}</h3>
                <p className="font-body text-xs text-ink-soft mt-1">
                  {new Date(n.created_at).toLocaleDateString()}
                </p>
              </div>
              <span
                className={
                  n.status === 'sent'
                    ? 'font-display font-semibold text-xs px-3 py-1 rounded-full bg-mustard text-ink'
                    : 'font-display font-semibold text-xs px-3 py-1 rounded-full bg-periwinkle text-ink'
                }
              >
                {n.status}
              </span>
            </button>
          ))}
        </div>
      )}

      {selected && (
        <div className="bg-white rounded-2xl p-6">
          <button
            onClick={() => setSelected(null)}
            className="font-display font-semibold text-sm text-cardinal mb-4"
          >
            Back to list
          </button>

          <label className="font-display font-semibold text-sm block mb-1">Subject</label>
          <input
            type="text"
            value={editSubject}
            onChange={(e) => setEditSubject(e.target.value)}
            disabled={selected.status === 'sent'}
            className="border border-periwinkle rounded-lg px-3 py-2 w-full mb-4 font-body text-sm"
          />

          <label className="font-display font-semibold text-sm block mb-1">HTML Content</label>
          <textarea
            value={editHtml}
            onChange={(e) => setEditHtml(e.target.value)}
            disabled={selected.status === 'sent'}
            rows={12}
            className="border border-periwinkle rounded-lg px-3 py-2 w-full font-mono text-xs mb-4"
          />

          {selected.status !== 'sent' && (
            <div className="flex flex-wrap gap-3">
              <button
                onClick={saveChanges}
                className="bg-periwinkle text-ink font-display font-semibold text-sm px-5 py-2 rounded-full hover:-translate-y-0.5 transition-transform"
              >
                Save Changes
              </button>
              {!confirmSend ? (
                <button
                  onClick={() => setConfirmSend(true)}
                  className="bg-cardinal text-white font-display font-semibold text-sm px-5 py-2 rounded-full hover:-translate-y-0.5 transition-transform"
                >
                  Send Newsletter
                </button>
              ) : (
                <div className="flex items-center gap-3 bg-cream rounded-full px-4 py-2">
                  <span className="font-body text-sm">Send to all active members?</span>
                  <button onClick={sendNewsletter} className="font-display font-semibold text-sm text-cardinal">
                    Yes, send
                  </button>
                  <button onClick={() => setConfirmSend(false)} className="font-display font-semibold text-sm text-ink-soft">
                    Cancel
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Newsletters

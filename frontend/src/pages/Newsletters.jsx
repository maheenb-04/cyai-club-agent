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
  const [viewMode, setViewMode] = useState('preview')
  const [testEmail, setTestEmail] = useState('')
  const [sendingTest, setSendingTest] = useState(false)
  const [attachments, setAttachments] = useState([])
  const [uploadingFile, setUploadingFile] = useState(false)

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

  function loadAttachments(newsletterId) {
    apiClient.get('/newsletters/' + newsletterId + '/attachments').then((res) => {
      setAttachments(res.data.filenames || [])
    })
  }

  function openNewsletter(n) {
    setSelected(n)
    setEditSubject(n.subject || '')
    setEditHtml(n.html_content || '')
    setConfirmSend(false)
    setViewMode('preview')
    setTestEmail('')
    loadAttachments(n.id)
  }

  function saveChanges() {
    apiClient
      .patch('/newsletters/' + selected.id, { subject: editSubject, html_content: editHtml })
      .then((res) => {
        setSelected(res.data)
        loadNewsletters()
      })
  }

  function handleFileUpload(e) {
    const file = e.target.files[0]
    if (!file) return
    setUploadingFile(true)
    const formData = new FormData()
    formData.append('file', file)
    apiClient
      .post('/newsletters/' + selected.id + '/attachments', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((res) => {
        setAttachments(res.data.filenames || [])
      })
      .finally(() => {
        setUploadingFile(false)
        e.target.value = ''
      })
  }

  function removeAttachment(filename) {
    apiClient.delete('/newsletters/' + selected.id + '/attachments/' + filename).then((res) => {
      setAttachments(res.data.filenames || [])
    })
  }

  function sendTestEmail() {
    if (!testEmail.trim()) return
    setSendingTest(true)
    apiClient
      .post('/newsletters/' + selected.id + '/send-test', { test_email: testEmail })
      .then((res) => {
        alert('Test email sent to ' + res.data.test_email + ' - check your inbox!')
      })
      .finally(() => setSendingTest(false))
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
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() => setSelected(null)}
              className="font-display font-semibold text-sm text-cardinal"
            >
              Back to list
            </button>
            <div className="flex gap-2">
              <button
                onClick={() => setViewMode('preview')}
                className={
                  viewMode === 'preview'
                    ? 'font-display font-semibold text-xs px-4 py-2 rounded-full bg-cardinal text-white'
                    : 'font-display font-semibold text-xs px-4 py-2 rounded-full bg-cream text-ink'
                }
              >
                Preview (Final Look)
              </button>
              <button
                onClick={() => setViewMode('edit')}
                className={
                  viewMode === 'edit'
                    ? 'font-display font-semibold text-xs px-4 py-2 rounded-full bg-cardinal text-white'
                    : 'font-display font-semibold text-xs px-4 py-2 rounded-full bg-cream text-ink'
                }
              >
                Edit HTML
              </button>
            </div>
          </div>

          <label className="font-display font-semibold text-sm block mb-1">Subject</label>
          <input
            type="text"
            value={editSubject}
            onChange={(e) => setEditSubject(e.target.value)}
            disabled={selected.status === 'sent'}
            className="border border-periwinkle rounded-lg px-3 py-2 w-full mb-4 font-body text-sm"
          />

          {viewMode === 'preview' && (
            <div className="mb-4">
              <p className="font-mono text-xs text-ink-soft mb-2">
                This is exactly how the newsletter will look when sent.
              </p>
              <div
                className="newsletter-preview border border-periwinkle rounded-lg p-6 bg-paper max-h-[600px] overflow-y-auto"
                dangerouslySetInnerHTML={{ __html: editHtml }}
              />
            </div>
          )}

          {viewMode === 'edit' && (
            <div className="mb-4">
              <label className="font-display font-semibold text-sm block mb-1">HTML Content</label>
              <textarea
                value={editHtml}
                onChange={(e) => setEditHtml(e.target.value)}
                disabled={selected.status === 'sent'}
                rows={16}
                className="border border-periwinkle rounded-lg px-3 py-2 w-full font-mono text-xs"
              />
            </div>
          )}

          <div className="bg-cream rounded-2xl p-4 mb-4">
            <p className="font-display font-semibold text-sm mb-2">Attachments (flyers, PDF newsletter, images)</p>
            <div className="space-y-2 mb-3">
              {attachments.map((filename) => (
                <div key={filename} className="flex items-center justify-between bg-white rounded-lg px-3 py-2">
                  <span className="font-body text-xs truncate flex-1">{filename.split('_').slice(2).join('_')}</span>
                  <button
                    onClick={() => removeAttachment(filename)}
                    className="font-display font-semibold text-xs text-cardinal ml-3 flex-shrink-0"
                  >
                    Remove
                  </button>
                </div>
              ))}
              {attachments.length === 0 && (
                <p className="font-body text-xs text-ink-soft">No attachments yet</p>
              )}
            </div>
            <label className="inline-block bg-periwinkle text-ink font-display font-semibold text-sm px-5 py-2 rounded-full hover:-translate-y-0.5 transition-transform cursor-pointer">
              {uploadingFile ? 'Uploading...' : '+ Attach File'}
              <input
                type="file"
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={handleFileUpload}
                disabled={uploadingFile}
                className="hidden"
              />
            </label>
          </div>

          <div className="bg-cream rounded-2xl p-4 mb-4">
            <p className="font-display font-semibold text-sm mb-2">Send a test email first</p>
            <div className="flex flex-col md:flex-row gap-3">
              <input
                type="email"
                placeholder="your.email@example.com"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                className="border border-periwinkle rounded-full px-4 py-2 font-body text-sm flex-1"
              />
              <button
                onClick={sendTestEmail}
                disabled={sendingTest || !testEmail.trim()}
                className="bg-periwinkle text-ink font-display font-semibold text-sm px-5 py-2 rounded-full hover:-translate-y-0.5 transition-transform disabled:opacity-50"
              >
                {sendingTest ? 'Sending...' : 'Send Test Email'}
              </button>
            </div>
          </div>

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

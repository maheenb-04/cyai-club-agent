import { useEffect, useState } from 'react'
import apiClient from '../api/client'

function Members() {
  const [members, setMembers] = useState([])
  const [newEmail, setNewEmail] = useState('')
  const [bulkText, setBulkText] = useState('')
  const [showBulk, setShowBulk] = useState(false)

  function loadMembers() {
    apiClient.get('/members/').then((res) => setMembers(res.data))
  }

  useEffect(() => {
    loadMembers()
  }, [])

  function handleAdd() {
    if (!newEmail.trim()) return
    apiClient.post('/members/', { email: newEmail.trim() }).then(() => {
      setNewEmail('')
      loadMembers()
    })
  }

  function handleBulkImport() {
    const emails = bulkText.split('\n').map((e) => e.trim()).filter((e) => e.length > 0)
    if (emails.length === 0) return
    apiClient.post('/members/bulk-import', emails).then((res) => {
      alert('Added ' + res.data.added + ', skipped ' + res.data.skipped_duplicates + ' duplicates')
      setBulkText('')
      setShowBulk(false)
      loadMembers()
    })
  }

  function handleDelete(id) {
    if (!confirm('Remove this member?')) return
    apiClient.delete('/members/' + id).then(() => loadMembers())
  }

  function handleExport() {
    apiClient.get('/members/export/csv', { responseType: 'blob' }).then((res) => {
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', 'cyai_members.csv')
      document.body.appendChild(link)
      link.click()
      link.remove()
    })
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <h2 className="font-display font-extrabold text-4xl">Members</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setShowBulk(!showBulk)}
            className="bg-periwinkle text-ink font-display font-semibold text-sm px-5 py-2 rounded-full hover:-translate-y-0.5 transition-transform"
          >
            Bulk Import
          </button>
          <button
            onClick={handleExport}
            className="bg-mustard text-ink font-display font-semibold text-sm px-5 py-2 rounded-full hover:-translate-y-0.5 transition-transform"
          >
            Export CSV
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl p-5 mb-4 flex flex-col md:flex-row gap-3">
        <input
          type="email"
          placeholder="member@yorkmail.cuny.edu"
          value={newEmail}
          onChange={(e) => setNewEmail(e.target.value)}
          className="border border-periwinkle rounded-full px-4 py-2 font-body text-sm flex-1"
        />
        <button
          onClick={handleAdd}
          className="bg-cardinal text-white font-display font-semibold text-sm px-5 py-2 rounded-full hover:-translate-y-0.5 transition-transform"
        >
          Add Member
        </button>
      </div>

      {showBulk && (
        <div className="bg-white rounded-2xl p-5 mb-6">
          <p className="font-display font-semibold text-sm mb-2">One email per line</p>
          <textarea
            value={bulkText}
            onChange={(e) => setBulkText(e.target.value)}
            rows={6}
            placeholder="member1@yorkmail.cuny.edu&#10;member2@yorkmail.cuny.edu"
            className="border border-periwinkle rounded-lg px-3 py-2 w-full font-mono text-sm mb-3"
          />
          <button
            onClick={handleBulkImport}
            className="bg-mustard text-ink font-display font-semibold text-sm px-5 py-2 rounded-full hover:-translate-y-0.5 transition-transform"
          >
            Import All
          </button>
        </div>
      )}

      <div className="bg-white rounded-2xl overflow-hidden">
        {members.map((m, idx) => (
          <div
            key={m.id}
            className={idx !== members.length - 1 ? 'flex items-center justify-between gap-4 px-5 py-3 border-b border-cream' : 'flex items-center justify-between gap-4 px-5 py-3'}
          >
            <div>
              <p className="font-body text-sm">{m.email}</p>
              {m.name && <p className="font-mono text-xs text-ink-soft">{m.name}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Members

import { useEffect, useState } from 'react'
import apiClient from '../api/client'

function Events() {
  const [events, setEvents] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    title: '',
    event_date: '',
    time_display: '',
    location: '',
    description: '',
    rsvp_link: '',
    event_type: 'meeting',
  })

  function loadEvents() {
    apiClient.get('/events/').then((res) => setEvents(res.data))
  }

  useEffect(() => {
    loadEvents()
  }, [])

  function handleChange(field, value) {
    setForm((f) => ({ ...f, [field]: value }))
  }

  function handleSubmit() {
    if (!form.title.trim()) return
    apiClient.post('/events/', form).then(() => {
      setForm({ title: '', event_date: '', time_display: '', location: '', description: '', rsvp_link: '', event_type: 'meeting' })
      setShowForm(false)
      loadEvents()
    })
  }

  function handleDelete(id) {
    if (!confirm('Remove this event?')) return
    apiClient.delete('/events/' + id).then(() => loadEvents())
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-display font-extrabold text-4xl">Events</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-cardinal text-white font-display font-semibold text-sm px-5 py-2 rounded-full hover:-translate-y-0.5 transition-transform"
        >
          {showForm ? 'Cancel' : '+ New Event'}
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-2xl p-6 mb-6 space-y-3">
          <input
            type="text"
            placeholder="Event title"
            value={form.title}
            onChange={(e) => handleChange('title', e.target.value)}
            className="border border-periwinkle rounded-lg px-3 py-2 w-full font-body text-sm"
          />
          <div className="grid grid-cols-2 gap-3">
            <input
              type="text"
              placeholder="Date (e.g. Tuesday, Aug 5th, 2026)"
              value={form.event_date}
              onChange={(e) => handleChange('event_date', e.target.value)}
              className="border border-periwinkle rounded-lg px-3 py-2 font-body text-sm"
            />
            <input
              type="text"
              placeholder="Time (e.g. 12:00-1:00 PM)"
              value={form.time_display}
              onChange={(e) => handleChange('time_display', e.target.value)}
              className="border border-periwinkle rounded-lg px-3 py-2 font-body text-sm"
            />
          </div>
          <input
            type="text"
            placeholder="Location"
            value={form.location}
            onChange={(e) => handleChange('location', e.target.value)}
            className="border border-periwinkle rounded-lg px-3 py-2 w-full font-body text-sm"
          />
          <textarea
            placeholder="Description"
            value={form.description}
            onChange={(e) => handleChange('description', e.target.value)}
            rows={3}
            className="border border-periwinkle rounded-lg px-3 py-2 w-full font-body text-sm"
          />
          <input
            type="text"
            placeholder="RSVP link (optional)"
            value={form.rsvp_link}
            onChange={(e) => handleChange('rsvp_link', e.target.value)}
            className="border border-periwinkle rounded-lg px-3 py-2 w-full font-body text-sm"
          />
          <button
            onClick={handleSubmit}
            className="bg-mustard text-ink font-display font-semibold text-sm px-5 py-2 rounded-full hover:-translate-y-0.5 transition-transform"
          >
            Create Event
          </button>
        </div>
      )}

      <div className="space-y-3">
        {events.map((ev) => (
          <div key={ev.id} className="bg-white rounded-2xl p-5 flex items-start justify-between gap-4">
            <div>
              <h3 className="font-display font-semibold text-lg">{ev.title}</h3>
              <p className="font-mono text-xs text-ink-soft mt-1">
                {ev.event_date || 'TBD'} - {ev.time_display || 'TBD'} - {ev.location || 'TBD'}
              </p>
              {ev.description && <p className="font-body text-sm mt-2">{ev.description}</p>}
            </div>
            <button
              onClick={() => handleDelete(ev.id)}
              className="font-display font-semibold text-xs text-cardinal flex-shrink-0"
            >
              Remove
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}

export default Events

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Award, Calendar, Users, Mail } from 'lucide-react'
import apiClient from '../api/client'

function StatTile({ to, count, label, colorClass, Icon }) {
  return (
    <Link to={to} className={'tile-base ' + colorClass}>
      <div className="icon-circle">
        <Icon size={22} />
      </div>
      <div>
        <div className="font-display font-extrabold text-5xl leading-none">{count}</div>
        <div className="font-display font-semibold text-sm mt-1">{label}</div>
      </div>
    </Link>
  )
}

function Dashboard() {
  const [counts, setCounts] = useState({ opportunities: null, events: null, members: null, newsletters: null })
  const [systemOk, setSystemOk] = useState(null)

  useEffect(() => {
    apiClient.get('/opportunities/').then((res) => setCounts((c) => ({ ...c, opportunities: res.data.length })))
    apiClient.get('/events/').then((res) => setCounts((c) => ({ ...c, events: res.data.length })))
    apiClient.get('/members/').then((res) => setCounts((c) => ({ ...c, members: res.data.length })))
    apiClient.get('/newsletters/').then((res) => setCounts((c) => ({ ...c, newsletters: res.data.length })))
    apiClient.get('/system/status').then((res) => setSystemOk(res.data.overall === 'all_systems_configured'))
  }, [])

  return (
    <div>
      <div className="arc-decoration arc-1"></div>
      <div className="arc-decoration arc-2"></div>

      <h2 className="font-display font-extrabold text-5xl mb-8 relative">
        Your club, <span className="text-cardinal">at a glance</span>
      </h2>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-5 relative">
        <StatTile to="/opportunities" count={counts.opportunities ?? '-'} label="Opportunities" colorClass="bg-cardinal text-white" Icon={Award} />
        <StatTile to="/events" count={counts.events ?? '-'} label="Upcoming Events" colorClass="bg-mustard text-ink" Icon={Calendar} />
        <StatTile to="/members" count={counts.members ?? '-'} label="Members" colorClass="bg-periwinkle text-ink" Icon={Users} />
        <StatTile to="/newsletters" count={counts.newsletters ?? '-'} label="Newsletters" colorClass="bg-ink text-cream" Icon={Mail} />
      </div>

      <div className="bg-white rounded-2xl px-6 py-4 mt-6 flex items-center gap-3 relative">
        <span className="status-pulse"></span>
        <p className="font-display font-semibold text-sm">
          {systemOk === null && 'Checking systems...'}
          {systemOk === true && 'All systems live'}
          {systemOk === false && 'Some systems need attention - check System page'}
        </p>
      </div>
    </div>
  )
}

export default Dashboard

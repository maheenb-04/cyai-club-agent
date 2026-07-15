import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Opportunities from './pages/Opportunities'
import Newsletters from './pages/Newsletters'
import Events from './pages/Events'
import Members from './pages/Members'
import SocialPosts from './pages/SocialPosts'
import SystemStatus from './pages/SystemStatus'

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/opportunities" element={<Opportunities />} />
        <Route path="/newsletters" element={<Newsletters />} />
        <Route path="/events" element={<Events />} />
        <Route path="/members" element={<Members />} />
        <Route path="/social" element={<SocialPosts />} />
        <Route path="/system" element={<SystemStatus />} />
      </Route>
    </Routes>
  )
}

export default App

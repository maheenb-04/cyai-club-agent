import { NavLink, Outlet } from 'react-router-dom'
import logo from '../assets/cyai-logo.png'

const navItems = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/opportunities', label: 'Opportunities' },
  { to: '/newsletters', label: 'Newsletters' },
  { to: '/events', label: 'Events' },
  { to: '/members', label: 'Members' },
  { to: '/social', label: 'Social Posts' },
  { to: '/system', label: 'System' },
]

function Layout() {
  return (
    <div className="min-h-screen bg-cream">
      <header className="bg-white shadow-sm px-6 md:px-8 py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <img src={logo} alt="CYAI Club Logo" className="w-12 h-12 rounded-full" />
          <h1 className="font-display font-extrabold text-2xl leading-none">
            CY<span className="text-cardinal">AI</span>
          </h1>
        </div>
        <nav className="flex flex-wrap gap-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                isActive
                  ? 'font-display font-semibold text-sm px-4 py-2 rounded-full transition-all duration-200 hover:-translate-y-0.5 bg-cardinal text-white'
                  : 'font-display font-semibold text-sm px-4 py-2 rounded-full transition-all duration-200 hover:-translate-y-0.5 bg-cream text-ink hover:bg-periwinkle'
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="p-6 md:p-10 relative overflow-hidden">
        <Outlet />
      </main>
    </div>
  )
}

export default Layout

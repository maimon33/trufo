import { NavLink } from 'react-router-dom'

export default function BottomNav() {
  return (
    <nav className="bottom-nav">
      <NavLink
        to="/"
        end
        className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
      >
        <span className="nav-icon">🔐</span>
        <span>Secrets</span>
      </NavLink>
      <NavLink
        to="/create"
        className={({ isActive }) => `nav-item${isActive ? ' active' : ''}`}
      >
        <span className="nav-icon">✏️</span>
        <span>Create</span>
      </NavLink>
    </nav>
  )
}

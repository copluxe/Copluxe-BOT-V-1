import { Link, useNavigate } from 'react-router-dom'

export default function Navbar() {
  const navigate = useNavigate()
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-50 glass border-b border-white/5">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <Link to="/dashboard" className="flex items-center gap-2 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-brand flex items-center justify-center">
            <span className="text-base">🎬</span>
          </div>
          <span className="text-lg font-bold gradient-text">PromoCut</span>
        </Link>

        <div className="flex items-center gap-4">
          <span className="text-white/50 text-sm hidden sm:block">
            {user.username || user.email}
          </span>
          <button
            onClick={logout}
            className="text-white/40 hover:text-white text-sm transition-colors px-3 py-1.5 rounded-lg hover:bg-white/5"
          >
            Déconnexion
          </button>
        </div>
      </div>
    </header>
  )
}

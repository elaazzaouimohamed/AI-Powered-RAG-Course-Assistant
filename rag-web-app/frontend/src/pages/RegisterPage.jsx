import { useState, useMemo } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { BookOpen, User, Mail, Lock } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm]     = useState({ username: '', email: '', password: '' })
  const [error, setError]   = useState('')
  const [loading, setLoading] = useState(false)

  const PARTICLE_ANIMS = ['animate-twinkle', 'animate-twinkle-2', 'animate-twinkle-3']
  const particles = useMemo(
    () => Array.from({ length: 22 }, (_, i) => ({
      top:  Math.random() * 100,
      left: Math.random() * 100,
      delay: Math.random() * 6,
      size: 2 + Math.random() * 3,
      anim: PARTICLE_ANIMS[i % PARTICLE_ANIMS.length],
    })),
    []
  )

  const submit = async e => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await register(form.username, form.email, form.password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.error || 'Erreur lors de l\'inscription')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden px-4">
      {/* ---- Fond immersif aurore ---- */}
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-900 via-teal-900 to-blue-950" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_18%_22%,rgba(16,185,129,.4),transparent_45%),radial-gradient(circle_at_82%_68%,rgba(37,99,235,.4),transparent_48%)]" />
      <div className="absolute -top-32 -left-24 w-[30rem] h-[30rem] rounded-full bg-emerald-500/20 blur-3xl animate-blob" />
      <div className="absolute -bottom-40 -right-24 w-[32rem] h-[32rem] rounded-full bg-blue-500/20 blur-3xl animate-blob-rev" />
      <div className="absolute top-1/3 left-1/2 w-72 h-72 rounded-full bg-teal-400/10 blur-3xl animate-blob" style={{ animationDelay: '5s' }} />
      {particles.map((p, i) => (
        <span key={i}
          className={`absolute rounded-full bg-white ${p.anim}`}
          style={{
            top: `${p.top}%`, left: `${p.left}%`,
            width: p.size, height: p.size,
            animationDelay: `${p.delay}s`,
          }} />
      ))}

      {/* ---- Carte glassmorphism ---- */}
      <div className="relative z-10 w-full max-w-md animate-fade-up">
        <div className="rounded-3xl border border-white/15 bg-white/10 backdrop-blur-2xl shadow-2xl shadow-black/40 px-8 sm:px-10 py-10">

          <div className="relative flex flex-col items-center mb-8">
            <div className="absolute -top-2 w-32 h-32 rounded-full bg-white/25 blur-2xl" />
            <div className="relative w-16 h-16 rounded-2xl bg-white/15 border border-white/20 backdrop-blur flex items-center justify-center animate-glow">
              <BookOpen className="w-8 h-8 text-white" />
            </div>
            <h1 className="relative mt-4 text-xl font-bold tracking-wide text-white">Créer un compte</h1>
            <p className="relative mt-1 text-xs font-medium tracking-[0.25em] text-white/60 uppercase">
              Rejoignez la plateforme
            </p>
          </div>

          <form onSubmit={submit} className="space-y-4">
            {error && (
              <div className="bg-red-500/15 border border-red-400/30 text-red-200 rounded-xl px-4 py-3 text-sm animate-fade-up">
                {error}
              </div>
            )}

            <div className="relative animate-fade-up delay-1">
              <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/50" />
              <input minLength={3}
                className="w-full bg-white/10 border border-white/15 text-white rounded-xl pl-12 pr-4 py-3.5
                           placeholder-white/50 focus:outline-none focus:border-white/40 focus:bg-white/15
                           focus:ring-2 focus:ring-white/20 transition-all"
                placeholder="Nom d'utilisateur"
                value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))} />
            </div>

            <div className="relative animate-fade-up delay-2">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/50" />
              <input type="email"
                className="w-full bg-white/10 border border-white/15 text-white rounded-xl pl-12 pr-4 py-3.5
                           placeholder-white/50 focus:outline-none focus:border-white/40 focus:bg-white/15
                           focus:ring-2 focus:ring-white/20 transition-all"
                placeholder="Adresse email"
                value={form.email}
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
            </div>

            <div className="relative animate-fade-up delay-3">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/50" />
              <input type="password" minLength={6}
                className="w-full bg-white/10 border border-white/15 text-white rounded-xl pl-12 pr-4 py-3.5
                           placeholder-white/50 focus:outline-none focus:border-white/40 focus:bg-white/15
                           focus:ring-2 focus:ring-white/20 transition-all"
                placeholder="Mot de passe (6 caractères min.)"
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
            </div>

            <div className="animate-fade-up delay-4 pt-1">
              <button type="submit" disabled={loading}
                className="w-full py-3.5 rounded-xl font-semibold tracking-wide text-white
                           bg-gradient-to-r from-emerald-500 via-teal-500 to-blue-600 animate-gradient
                           shadow-lg shadow-blue-900/40 transition-all hover:-translate-y-0.5
                           hover:shadow-xl hover:shadow-blue-900/50 active:translate-y-0
                           disabled:opacity-60 disabled:cursor-not-allowed">
                {loading ? 'CRÉATION…' : 'CRÉER LE COMPTE'}
              </button>
            </div>
          </form>

          <div className="mt-6 border-t border-white/10" />
          <p className="text-center text-white/60 text-sm mt-4 animate-fade-up delay-5">
            Déjà un compte ?{' '}
            <Link to="/login" className="text-white hover:text-white/80 font-medium">Se connecter</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

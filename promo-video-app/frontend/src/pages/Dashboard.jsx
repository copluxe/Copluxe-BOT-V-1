import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import PhotoUploader from '../components/PhotoUploader'
import { videoAPI } from '../lib/api'

const EXAMPLE_DESCRIPTIONS = [
  'Clips de luxury bags avec cuts rapides, style californien, texte blanc gras, ambiance hype 🔥',
  'Sneakers drop ultra dynamique, cuts ultra rapides, texte doré, vibe streetwear NY',
  'Collection été — robes fluides, zoom doux, texte blanc élégant, ambiance chill beach',
  'Promotion restaurant gastronomique, slides lents, typographie dorée, ambiance prestige',
]

export default function Dashboard() {
  const navigate = useNavigate()
  const [photos, setPhotos] = useState([])
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [error, setError] = useState('')
  const [myVideos, setMyVideos] = useState([])
  const [loadingVideos, setLoadingVideos] = useState(true)
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  useEffect(() => {
    loadMyVideos()
  }, [])

  async function loadMyVideos() {
    try {
      const { data } = await videoAPI.myVideos()
      setMyVideos(data)
    } catch {
      // ignore
    } finally {
      setLoadingVideos(false)
    }
  }

  async function handleGenerate(e) {
    e.preventDefault()
    setError('')

    if (photos.length < 3) {
      setError('Ajoute au moins 3 photos pour générer ta vidéo.')
      return
    }
    if (!description.trim()) {
      setError('Décris le style de vidéo que tu veux.')
      return
    }

    setLoading(true)
    setUploadProgress(0)

    try {
      const formData = new FormData()
      formData.append('description', description)
      photos.forEach(p => formData.append('files', p.file))

      const { data } = await videoAPI.generate(formData, (progressEvent) => {
        const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total)
        setUploadProgress(pct)
      })

      navigate(`/result/${data.video_id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la génération. Réessaie.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-dark-950">
      <Navbar />

      <main className="max-w-3xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Hero */}
        <div className="text-center animate-fade-in">
          <h1 className="text-4xl sm:text-5xl font-black text-white mb-3">
            Crée ta vidéo promo{' '}
            <span className="gradient-text">en 1 clic</span>
          </h1>
          <p className="text-white/50 text-lg">
            Envoie tes photos, décris ton style — on génère une vidéo MP4 prête pour TikTok.
          </p>
        </div>

        {/* Main form */}
        <form onSubmit={handleGenerate} className="space-y-6 animate-slide-up">
          {/* Step 1: Photos */}
          <div className="card">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-8 h-8 rounded-lg bg-gradient-brand flex items-center justify-center text-white font-bold text-sm">
                1
              </div>
              <div>
                <h2 className="text-white font-semibold">Tes photos</h2>
                <p className="text-white/40 text-sm">Entre 3 et 10 photos (JPG, PNG, WebP)</p>
              </div>
            </div>
            <PhotoUploader photos={photos} onPhotosChange={setPhotos} />
          </div>

          {/* Step 2: Description */}
          <div className="card">
            <div className="flex items-center gap-3 mb-5">
              <div className="w-8 h-8 rounded-lg bg-gradient-brand flex items-center justify-center text-white font-bold text-sm">
                2
              </div>
              <div>
                <h2 className="text-white font-semibold">Décris ton style</h2>
                <p className="text-white/40 text-sm">Plus c'est précis, mieux c'est</p>
              </div>
            </div>

            <textarea
              className="input-field min-h-[120px] resize-none"
              placeholder="Ex: clips de luxury bags avec cuts rapides, style californien, texte blanc gras, ambiance hype..."
              value={description}
              onChange={e => setDescription(e.target.value)}
              maxLength={500}
            />
            <div className="flex justify-between items-center mt-2">
              <p className="text-white/20 text-xs">{description.length}/500</p>
            </div>

            {/* Example chips */}
            <div className="mt-4">
              <p className="text-white/30 text-xs mb-2">Exemples rapides :</p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLE_DESCRIPTIONS.map((ex, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => setDescription(ex)}
                    className="text-xs px-3 py-1.5 rounded-full bg-white/5 hover:bg-white/10 text-white/50 hover:text-white/80 transition-all border border-white/10 text-left"
                  >
                    {ex.slice(0, 50)}…
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm animate-fade-in">
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={loading || photos.length < 3 || !description.trim()}
            className="btn-primary w-full py-4 text-base flex items-center justify-center gap-3"
          >
            {loading ? (
              <>
                <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {uploadProgress < 100 ? `Upload... ${uploadProgress}%` : 'Démarrage de la génération...'}
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M15 10l4.553-2.069A1 1 0 0121 8.879V15.12a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
                Générer ma vidéo promo 🚀
              </>
            )}
          </button>

          {loading && uploadProgress < 100 && (
            <div className="w-full bg-white/10 rounded-full h-1.5 overflow-hidden">
              <div
                className="h-full bg-gradient-brand transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          )}
        </form>

        {/* My past videos */}
        {!loadingVideos && myVideos.length > 0 && (
          <section className="animate-slide-up">
            <h3 className="text-white/60 text-sm font-medium mb-4 flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                />
              </svg>
              Mes vidéos récentes
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {myVideos.slice(0, 6).map(v => (
                <Link
                  key={v.id}
                  to={`/result/${v.id}`}
                  className="group glass rounded-xl overflow-hidden hover:border-brand-purple/40 transition-all"
                >
                  <div className="aspect-tiktok bg-dark-900 relative">
                    {v.thumbnail_url ? (
                      <img src={v.thumbnail_url} alt="thumbnail" className="w-full h-full object-cover" />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <span className="text-2xl">
                          {v.status === 'processing' ? '⏳' : v.status === 'failed' ? '❌' : '🎬'}
                        </span>
                      </div>
                    )}
                    <div className={`absolute top-2 right-2 text-xs px-2 py-0.5 rounded-full ${
                      v.status === 'completed' ? 'bg-green-500/80 text-white' :
                      v.status === 'processing' ? 'bg-yellow-500/80 text-black' :
                      v.status === 'failed' ? 'bg-red-500/80 text-white' :
                      'bg-white/20 text-white'
                    }`}>
                      {v.status === 'completed' ? '✓' : v.status === 'processing' ? '...' : v.status === 'failed' ? '✗' : '⏳'}
                    </div>
                  </div>
                  <div className="p-2">
                    <p className="text-white/60 text-xs line-clamp-2">{v.description}</p>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}

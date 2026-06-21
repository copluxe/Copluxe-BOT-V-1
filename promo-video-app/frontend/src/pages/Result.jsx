import { useEffect, useState, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import Navbar from '../components/Navbar'
import VideoPlayer from '../components/VideoPlayer'
import LoadingScreen from '../components/LoadingScreen'
import { videoAPI } from '../lib/api'

const POLL_INTERVAL = 3000

export default function Result() {
  const { videoId } = useParams()
  const [videoData, setVideoData] = useState(null)
  const [error, setError] = useState('')
  const [regenerating, setRegenerating] = useState(false)
  const pollRef = useRef(null)

  useEffect(() => {
    fetchStatus()
    return () => clearInterval(pollRef.current)
  }, [videoId])

  async function fetchStatus() {
    try {
      const { data } = await videoAPI.getStatus(videoId)
      setVideoData(data)

      if (data.status === 'pending' || data.status === 'processing') {
        pollRef.current = setTimeout(fetchStatus, POLL_INTERVAL)
      } else {
        clearInterval(pollRef.current)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors du chargement')
    }
  }

  async function handleRegenerate() {
    setRegenerating(true)
    setError('')
    try {
      await videoAPI.regenerate(videoId)
      setVideoData(d => ({ ...d, status: 'pending', output_url: null, thumbnail_url: null }))
      clearInterval(pollRef.current)
      setTimeout(fetchStatus, 1000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur lors de la régénération')
    } finally {
      setRegenerating(false)
    }
  }

  function handleDownload() {
    if (!videoData?.output_url) return
    const a = document.createElement('a')
    a.href = videoData.output_url
    a.download = `promo_video_${videoId}.mp4`
    a.click()
  }

  const isLoading = !videoData || videoData.status === 'pending' || videoData.status === 'processing'
  const isCompleted = videoData?.status === 'completed'
  const isFailed = videoData?.status === 'failed'

  return (
    <div className="min-h-screen bg-dark-950">
      <Navbar />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        {/* Back link */}
        <Link
          to="/dashboard"
          className="inline-flex items-center gap-2 text-white/40 hover:text-white/80 text-sm mb-6 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Retour
        </Link>

        {/* Loading state */}
        {isLoading && (
          <div className="card animate-fade-in">
            <LoadingScreen status={videoData?.status} />
          </div>
        )}

        {/* Failed state */}
        {isFailed && (
          <div className="card text-center py-12 animate-fade-in">
            <div className="text-5xl mb-4">😞</div>
            <h2 className="text-xl font-bold text-white mb-2">La génération a échoué</h2>
            <p className="text-white/40 mb-6 text-sm">
              {videoData?.error_message || 'Une erreur inattendue est survenue.'}
            </p>
            <div className="flex gap-3 justify-center">
              <button onClick={handleRegenerate} disabled={regenerating} className="btn-primary">
                {regenerating ? 'Régénération...' : 'Réessayer'}
              </button>
              <Link to="/dashboard" className="btn-secondary">Nouveau projet</Link>
            </div>
          </div>
        )}

        {/* Completed state */}
        {isCompleted && videoData && (
          <div className="animate-fade-in">
            {/* Success banner */}
            <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-2xl flex items-center gap-3">
              <span className="text-2xl">🎉</span>
              <div>
                <p className="text-green-400 font-semibold">Ta vidéo promo est prête !</p>
                <p className="text-green-400/60 text-sm">
                  {videoData.duration ? `Durée : ${videoData.duration}s • ` : ''}Format TikTok 9:16 MP4
                </p>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-8 items-start">
              {/* Video player */}
              <div>
                <VideoPlayer
                  src={videoData.output_url}
                  thumbnail={videoData.thumbnail_url}
                />
              </div>

              {/* Actions & info */}
              <div className="space-y-5">
                <div className="card">
                  <h3 className="text-white font-semibold mb-1">Description</h3>
                  <p className="text-white/50 text-sm">{videoData.description}</p>
                </div>

                {/* Download */}
                <button
                  onClick={handleDownload}
                  className="btn-primary w-full py-4 flex items-center justify-center gap-3"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  Télécharger le MP4
                </button>

                {/* Regenerate */}
                <button
                  onClick={handleRegenerate}
                  disabled={regenerating}
                  className="btn-secondary w-full py-3 flex items-center justify-center gap-2"
                >
                  {regenerating ? (
                    <>
                      <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Régénération...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                        />
                      </svg>
                      Générer une variation
                    </>
                  )}
                </button>

                <p className="text-white/25 text-xs text-center">
                  Une variation utilise les mêmes photos avec des transitions et textes différents
                </p>

                {/* New project */}
                <Link to="/dashboard" className="block text-center text-white/40 hover:text-white/70 text-sm transition-colors">
                  + Nouveau projet
                </Link>
              </div>
            </div>
          </div>
        )}

        {/* Global error */}
        {error && (
          <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 text-red-400 text-sm">
            {error}
          </div>
        )}
      </main>
    </div>
  )
}

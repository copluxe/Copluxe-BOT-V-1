import { useEffect, useState } from 'react'

const STEPS = [
  { label: 'Analyse de tes photos...', duration: 15 },
  { label: 'Création de la timeline...', duration: 25 },
  { label: 'Application des transitions...', duration: 40 },
  { label: 'Génération des textes...', duration: 55 },
  { label: 'Ajout de la musique...', duration: 70 },
  { label: 'Encodage MP4 final...', duration: 90 },
  { label: 'Finalisation...', duration: 98 },
]

export default function LoadingScreen({ status }) {
  const [progress, setProgress] = useState(5)
  const [currentStep, setCurrentStep] = useState(0)
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(e => {
        const next = e + 1
        // Simulate progress based on time
        const targetProgress = Math.min(95, 5 + next * 1.5)
        setProgress(targetProgress)

        // Update step
        const stepIdx = STEPS.findIndex(s => s.duration > targetProgress)
        if (stepIdx > 0) setCurrentStep(stepIdx - 1)
        else if (stepIdx === -1) setCurrentStep(STEPS.length - 1)

        return next
      })
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (status === 'completed') setProgress(100)
  }, [status])

  const step = STEPS[currentStep]

  return (
    <div className="flex flex-col items-center py-16 px-4 animate-fade-in">
      {/* Animated icon */}
      <div className="relative w-32 h-32 mb-8">
        <div className="absolute inset-0 rounded-full bg-gradient-brand opacity-20 animate-ping" />
        <div className="absolute inset-4 rounded-full bg-gradient-brand opacity-30 animate-pulse" />
        <div className="absolute inset-8 rounded-full bg-gradient-brand flex items-center justify-center">
          <svg className="w-8 h-8 text-white animate-spin-slow" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M15 10l4.553-2.069A1 1 0 0121 8.879V15.12a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
        </div>
      </div>

      <h2 className="text-2xl font-bold text-white mb-2">Génération en cours...</h2>
      <p className="text-white/50 text-center mb-8 max-w-sm">
        Ta vidéo promo est en train d'être créée. Ça peut prendre 1 à 3 minutes.
      </p>

      {/* Progress bar */}
      <div className="w-full max-w-md mb-4">
        <div className="flex justify-between text-sm text-white/40 mb-2">
          <span>{step?.label}</span>
          <span>{Math.round(progress)}%</span>
        </div>
        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-brand rounded-full transition-all duration-1000 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="flex gap-2 mt-4">
        {STEPS.map((s, i) => (
          <div
            key={i}
            className={`w-2 h-2 rounded-full transition-all duration-300 ${
              i <= currentStep ? 'bg-brand-purple' : 'bg-white/15'
            }`}
          />
        ))}
      </div>

      <p className="text-white/20 text-xs mt-6">
        Temps écoulé : {Math.floor(elapsed / 60)}:{String(elapsed % 60).padStart(2, '0')}
      </p>
    </div>
  )
}

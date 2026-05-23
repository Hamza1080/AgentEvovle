'use client'

import { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

// ─── Status phases ────────────────────────────────────────────────────────────
const PHASES = [
  {
    text: 'Initializing MAS engine...',
    subtext: 'Bootstrapping expert agent network across distributed compute nodes.',
    icon: 'server',
  },
  {
    text: 'Verifying geographical requirements...',
    subtext: 'Cross-checking city pairs, route viability, and regional constraints.',
    icon: 'globe',
  },
  {
    text: 'Structuring itinerary inputs...',
    subtext: 'Parsing traveler profile, preferences, and temporal constraints.',
    icon: 'grid',
  },
  {
    text: 'Drafting initial proposal...',
    subtext: 'Generating baseline itinerary using historical optimization data.',
    icon: 'document',
  },
  {
    text: 'Cross-referencing budget constraints...',
    subtext: 'Running economic feasibility checks across accommodation and dining tiers.',
    icon: 'balance',
  },
  {
    text: 'Refining solution via expert agents...',
    subtext: 'Multi-agent negotiation in progress. Agents are resolving trade-off conflicts.',
    icon: 'nodes',
  },
  {
    text: 'Finalizing travel nodes...',
    subtext: 'Locking in optimal stops, transportation chains, and booking windows.',
    icon: 'pin',
  },
  {
    text: 'Almost ready...',
    subtext: 'Final validation pass. Compiling your personalized travel report.',
    icon: 'check',
  },
]

// ─── SVG Icons ─────────────────────────────────────────────────────────────────
function PhaseIcon({ icon, className = '' }: { icon: string; className?: string }) {
  const base = `w-8 h-8 text-[#8CA090] ${className}`
  const s = { strokeWidth: '1.4', strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const }

  switch (icon) {
    case 'server':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className={base}>
          <rect x="2" y="3" width="20" height="5" rx="2" {...s}/>
          <rect x="2" y="10" width="20" height="5" rx="2" {...s}/>
          <rect x="2" y="17" width="20" height="4" rx="2" {...s}/>
          <circle cx="18" cy="5.5" r="1" fill="currentColor"/>
          <circle cx="18" cy="12.5" r="1" fill="currentColor"/>
        </svg>
      )
    case 'globe':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className={base}>
          <circle cx="12" cy="12" r="9" {...s}/>
          <ellipse cx="12" cy="12" rx="4" ry="9" {...s}/>
          <path d="M3 9h18M3 15h18" {...s}/>
        </svg>
      )
    case 'grid':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className={base}>
          <rect x="3" y="3" width="7" height="7" rx="1.5" {...s}/>
          <rect x="14" y="3" width="7" height="7" rx="1.5" {...s}/>
          <rect x="3" y="14" width="7" height="7" rx="1.5" {...s}/>
          <rect x="14" y="14" width="7" height="7" rx="1.5" {...s}/>
        </svg>
      )
    case 'document':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className={base}>
          <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" {...s}/>
          <path d="M14 2v6h6" {...s}/>
          <path d="M8 13h8M8 17h5" {...s}/>
        </svg>
      )
    case 'balance':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className={base}>
          <path d="M12 3v18" {...s}/>
          <path d="M8 21h8" {...s}/>
          <path d="M5 8L2 14h6L5 8z" {...s}/>
          <path d="M19 8l-3 6h6l-3-6z" {...s}/>
          <path d="M5 8h14" {...s}/>
        </svg>
      )
    case 'nodes':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className={base}>
          <circle cx="12" cy="5" r="2.5" {...s}/>
          <circle cx="5" cy="18" r="2.5" {...s}/>
          <circle cx="19" cy="18" r="2.5" {...s}/>
          <path d="M12 7.5L5 15.5M12 7.5L19 15.5M5 18h14" {...s}/>
        </svg>
      )
    case 'pin':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className={base}>
          <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" {...s}/>
          <circle cx="12" cy="9" r="2.5" {...s}/>
        </svg>
      )
    case 'check':
      return (
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className={base}>
          <circle cx="12" cy="12" r="9" {...s}/>
          <path d="M8 12l3 3 5-5" {...s}/>
        </svg>
      )
    default:
      return null
  }
}

// ─── Orbital Loader ────────────────────────────────────────────────────────────
function OrbitalLoader() {
  return (
    <div className="relative w-40 h-40 flex items-center justify-center">
      {/* Outer ring */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-0 rounded-full"
        style={{
          border: '1px solid rgba(140,160,144,0.15)',
          boxShadow: 'inset 0 0 20px rgba(140,160,144,0.03)',
        }}
      >
        {/* Orbital dot */}
        <div
          className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-[#8CA090]"
          style={{ boxShadow: '0 0 8px 2px rgba(140,160,144,0.6)' }}
        />
      </motion.div>

      {/* Middle ring */}
      <motion.div
        animate={{ rotate: -360 }}
        transition={{ duration: 5, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-4 rounded-full"
        style={{ border: '1px solid rgba(107,143,160,0.2)' }}
      >
        <div
          className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-1.5 h-1.5 rounded-full bg-[#6B8FA0]"
          style={{ boxShadow: '0 0 6px 2px rgba(107,143,160,0.5)' }}
        />
      </motion.div>

      {/* Inner ring */}
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-8 rounded-full"
        style={{ border: '1px dashed rgba(140,160,144,0.12)' }}
      />

      {/* Center pulse */}
      <div className="relative">
        <motion.div
          animate={{ scale: [1, 1.4, 1], opacity: [0.4, 0, 0.4] }}
          transition={{ duration: 2.5, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute inset-0 rounded-full bg-[#8CA090]/20 -m-3"
        />
        <div
          className="w-6 h-6 rounded-full bg-[#8CA090]/80"
          style={{ boxShadow: '0 0 16px 4px rgba(140,160,144,0.3)' }}
        />
      </div>
    </div>
  )
}

// ─── Progress Bar ──────────────────────────────────────────────────────────────
function GlowProgressBar({ progress }: { progress: number }) {
  return (
    <div className="w-full h-0.5 bg-[#1C2126] rounded-full overflow-hidden">
      <motion.div
        className="h-full rounded-full"
        style={{
          background: 'linear-gradient(90deg, #4A5D4E, #8CA090, #6B8FA0)',
          width: `${progress}%`,
          boxShadow: '0 0 12px 2px rgba(140,160,144,0.4)',
        }}
        transition={{ duration: 1, ease: 'easeOut' }}
      />
    </div>
  )
}

// ─── Main Component ────────────────────────────────────────────────────────────
interface LoadingScreenProps {
  tripDetails?: {
    origin: string
    destination: string
    travelers: number
    masStrategy: 'budget' | 'experience'
  }
  onComplete: () => void
}

// ─── Agent log messages (module-level — stable reference, avoids Strict Mode issues) ──────
const LOG_MESSAGES: string[] = [
  '[agent:router] Received planning request. Broadcasting to agent pool...',
  '[agent:geo] Validating origin/destination pair...',
  '[agent:geo] Route feasibility: PASS. Distance computed.',
  '[agent:profile] Parsing traveler preferences and constraints...',
  '[agent:timeline] Building date-aware availability windows...',
  '[agent:budget] Initializing cost modeling engine...',
  '[agent:accommodation] Querying lodging database...',
  '[agent:accommodation] Ranked 142 options. Filtering by house rules...',
  '[agent:dining] Loading cuisine preference vectors...',
  '[agent:dining] Computed match scores for 87 establishments.',
  '[agent:transport] Optimizing transport chains between nodes...',
  '[agent:council] All agents reporting. Initiating consensus round 1...',
  '[agent:council] Conflict detected: budget vs. experience weight. Resolving...',
  '[agent:council] Resolution: applying weighted compromise at 0.67 threshold.',
  '[agent:quality] Running final itinerary validation pass...',
  '[agent:quality] Schema checks: PASS. Constraint satisfaction: PASS.',
  '[agent:router] Itinerary finalized. Preparing output payload...',
]

export function LoadingScreen({ tripDetails, onComplete }: LoadingScreenProps) {
  const [phaseIndex, setPhaseIndex] = useState(0)
  const [progress, setProgress] = useState(0)
  const [elapsed, setElapsed] = useState(0)
  const [agentLogs, setAgentLogs] = useState<string[]>([])
  const totalDuration = 210_000 // 3.5 minutes
  const logRef = useRef<HTMLDivElement>(null)
  // Use a ref for the drip index so it is never mutated inside a state updater
  // (React Strict Mode can call state updaters twice, which would corrupt a plain `let i`)
  const dripIndexRef = useRef(0)

  // Progress ticker (runs every 500ms)
  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed(prev => {
        const next = prev + 500
        const pct = Math.min((next / totalDuration) * 100, 98)
        setProgress(pct)
        if (next >= totalDuration) {
          clearInterval(interval)
          setProgress(100)
          setTimeout(onComplete, 600)
        }
        return next
      })
    }, 500)
    return () => clearInterval(interval)
  }, [onComplete])

  // Phase cycling
  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>
    const schedule = () => {
      const delay = 15_000 + Math.random() * 15_000 // 15–30s
      timeout = setTimeout(() => {
        setPhaseIndex(prev => {
          const next = Math.min(prev + 1, PHASES.length - 1)
          return next
        })
        schedule()
      }, delay)
    }
    schedule()
    return () => clearTimeout(timeout)
  }, [])

  // Agent log drip — index stored in a ref to survive Strict Mode double-invocation
  useEffect(() => {
    dripIndexRef.current = 0
    let timeoutId: ReturnType<typeof setTimeout>
    const next = () => {
      const idx = dripIndexRef.current
      if (idx >= LOG_MESSAGES.length) return
      const msg = LOG_MESSAGES[idx]
      if (typeof msg === 'string') {
        dripIndexRef.current = idx + 1
        setAgentLogs(prev => [...prev, msg])
      }
      timeoutId = setTimeout(next, 7_000 + Math.random() * 8_000)
    }
    timeoutId = setTimeout(next, 1500)
    return () => clearTimeout(timeoutId)
  }, [])

  // Keep log scrolled
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight
    }
  }, [agentLogs])

  const phase = PHASES[phaseIndex]
  const timeRemaining = Math.max(0, totalDuration - elapsed)
  const minutesLeft = Math.floor(timeRemaining / 60_000)
  const secondsLeft = Math.floor((timeRemaining % 60_000) / 1000)

  return (
    <div
      className="min-h-screen bg-[#0D1114] flex flex-col"
      style={{ fontFamily: 'Inter, SF Pro Display, system-ui, sans-serif' }}
    >
      {/* Top progress bar */}
      <div className="fixed top-0 left-0 right-0 z-50">
        <GlowProgressBar progress={progress} />
      </div>

      {/* Header */}
      <header className="border-b border-[#1C2126] bg-[#0D1114]/90 backdrop-blur-xl px-6 py-4">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#8CA090] to-[#6B8FA0] flex items-center justify-center">
              <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4">
                <circle cx="8" cy="8" r="6" stroke="#121619" strokeWidth="1.5"/>
                <path d="M8 4v4l2.5 2" stroke="#121619" strokeWidth="1.3" strokeLinecap="round"/>
              </svg>
            </div>
            <span className="text-sm font-semibold text-[#F9F9F7]">EvoAgent</span>
          </div>
          <div className="flex items-center gap-4 text-[11px] text-[#6A7175]">
            <div className="flex items-center gap-1.5">
              <motion.span
                animate={{ opacity: [1, 0.3, 1] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="w-1.5 h-1.5 rounded-full bg-[#8CA090]"
              />
              Processing
            </div>
            <span className="text-[#4A5560]">·</span>
            <span>
              ~{minutesLeft}m {secondsLeft.toString().padStart(2, '0')}s remaining
            </span>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-16 max-w-5xl mx-auto w-full">

        {/* Trip info chip */}
        {tripDetails && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-12 flex items-center gap-3 bg-[#1C2126] border border-[#313A43] rounded-2xl px-5 py-3"
          >
            <span className="text-sm font-medium text-[#F9F9F7]">{tripDetails.origin}</span>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="w-4 h-4 text-[#8CA090]">
              <path d="M5 12h14M13 6l6 6-6 6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span className="text-sm font-medium text-[#F9F9F7]">{tripDetails.destination}</span>
            <div className="w-px h-4 bg-[#313A43] mx-1" />
            <span className="text-[11px] text-[#9CA3AF]">{tripDetails.travelers} travelers</span>
            <div className="w-px h-4 bg-[#313A43] mx-1" />
            <span className="text-[11px] px-2 py-0.5 rounded-lg bg-[#8CA090]/10 text-[#8CA090]">
              {tripDetails.masStrategy === 'budget' ? 'Budget First' : 'Experience First'}
            </span>
          </motion.div>
        )}

        {/* Orbital loader */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          className="mb-12"
        >
          <OrbitalLoader />
        </motion.div>

        {/* Phase display */}
        <div className="w-full max-w-lg space-y-5 text-center">
          <AnimatePresence mode="wait">
            <motion.div
              key={phaseIndex}
              initial={{ opacity: 0, y: 12, filter: 'blur(4px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              exit={{ opacity: 0, y: -12, filter: 'blur(4px)' }}
              transition={{ duration: 0.4 }}
              className="space-y-3"
            >
              {/* Icon + Phase index */}
              <div className="flex items-center justify-center gap-3">
                <motion.div
                  initial={{ rotate: -10, scale: 0.8 }}
                  animate={{ rotate: 0, scale: 1 }}
                  transition={{ type: 'spring', stiffness: 300 }}
                >
                  <PhaseIcon icon={phase.icon} />
                </motion.div>
                <span className="text-[10px] font-bold tracking-[0.3em] text-[#8CA090] uppercase">
                  Phase {phaseIndex + 1} / {PHASES.length}
                </span>
              </div>
              <h2 className="text-xl font-semibold text-[#F9F9F7] tracking-tight">
                {phase.text}
              </h2>
              <p className="text-sm text-[#6A7175] leading-relaxed max-w-sm mx-auto">
                {phase.subtext}
              </p>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Agent log terminal */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mt-12 w-full max-w-2xl"
        >
          <div className="bg-[#0A0D0F] border border-[#1C2126] rounded-2xl overflow-hidden">
            {/* Terminal header */}
            <div className="flex items-center gap-2 px-5 py-3 border-b border-[#1C2126] bg-[#0D1114]">
              <div className="flex gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-[#FF5F56]/40" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#FFBD2E]/40" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#27C93F]/40" />
              </div>
              <span className="text-[11px] text-[#4A5560] ml-2 font-mono tracking-wide">evoagent — mas-runtime</span>
              <div className="ml-auto flex items-center gap-1.5">
                <motion.span
                  animate={{ opacity: [1, 0, 1] }}
                  transition={{ duration: 1, repeat: Infinity }}
                  className="text-[10px] font-mono text-[#8CA090]"
                >
                  ▌
                </motion.span>
              </div>
            </div>
            {/* Log body */}
            <div
              ref={logRef}
              className="h-48 overflow-y-auto p-5 space-y-2 scroll-smooth"
              style={{ scrollbarWidth: 'none' }}
            >
              {agentLogs.map((log, i) => (
                <motion.p
                  key={i}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="text-[11px] font-mono leading-relaxed"
                >
                  <span className="text-[#4A5560]">{String(i + 1).padStart(3, '0')}  </span>
                  <span className={
                    log?.includes('[agent:council]') ? 'text-[#8CA090]' :
                    log?.includes('[agent:quality]') ? 'text-[#6B8FA0]' :
                    log?.includes('PASS') ? 'text-[#8CA090]/80' :
                    'text-[#6A7175]'
                  }>{log ?? ''}</span>
                </motion.p>
              ))}
              {agentLogs.length === 0 && (
                <p className="text-[11px] font-mono text-[#4A5560]">Waiting for agent output...</p>
              )}
            </div>
          </div>
        </motion.div>

        {/* Phase indicators */}
        <div className="mt-10 flex items-center gap-2">
          {PHASES.map((_, i) => (
            <motion.div
              key={i}
              className={`rounded-full transition-all duration-500 ${
                i === phaseIndex
                  ? 'w-6 h-1.5 bg-[#8CA090]'
                  : i < phaseIndex
                  ? 'w-1.5 h-1.5 bg-[#8CA090]/40'
                  : 'w-1.5 h-1.5 bg-[#313A43]'
              }`}
              style={i === phaseIndex ? { boxShadow: '0 0 8px rgba(140,160,144,0.5)' } : {}}
            />
          ))}
        </div>

        <p className="mt-6 text-[11px] text-[#4A5560] tracking-wide text-center">
          You can safely leave this page — your plan will be ready when you return.
        </p>
      </div>
    </div>
  )
}

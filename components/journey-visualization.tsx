'use client'

import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import gsap from 'gsap'
import { MapPin, Clock, DollarSign } from 'lucide-react'

interface JourneyVisualizationProps {
  travelData: {
    org: string
    dest: string
    days: number
    itinerary: Array<{
      day: number
      current_city: string
      transportation: string
    }>
  }
}

const cities = [
  { id: 'provo', name: 'Provo', x: '15%', y: '50%', color: 'from-blue-500 to-blue-600' },
  { id: 'phoenix', name: 'Phoenix', x: '50%', y: '50%', color: 'from-cyan-500 to-cyan-600' },
  { id: 'provo-return', name: 'Provo', x: '85%', y: '50%', color: 'from-blue-500 to-blue-600', isReturn: true },
]

export function JourneyVisualization({ travelData }: JourneyVisualizationProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (svgRef.current) {
      const paths = svgRef.current.querySelectorAll('path')
      paths.forEach((path, idx) => {
        const length = path.getTotalLength()
        path.setAttribute('stroke-dasharray', length.toString())
        path.setAttribute('stroke-dashoffset', length.toString())

        gsap.to(path, {
          strokeDashoffset: 0,
          duration: 2.5,
          delay: idx * 0.3,
          ease: 'power2.inOut',
        })
      })
    }

    // Animate nodes
    const nodes = containerRef.current?.querySelectorAll('[data-node]')
    if (nodes) {
      nodes.forEach((node, idx) => {
        gsap.fromTo(
          node,
          { scale: 0, opacity: 0 },
          {
            scale: 1,
            opacity: 1,
            duration: 0.6,
            delay: 0.5 + idx * 0.2,
            ease: 'back.out',
          }
        )
      })
    }
  }, [])

  const parseTransportation = (transport: string) => {
    const match = transport.match(/(\d+)\s*(?:hours?|hrs?)?(?:\s*(\d+))?\s*(?:mins?)?/)
    if (match) {
      const hours = parseInt(match[1])
      const minutes = match[2] ? parseInt(match[2]) : 0
      return { hours, minutes, total: `${hours}h ${minutes}m` }
    }
    return { hours: 0, minutes: 0, total: 'Unknown' }
  }

  return (
    <div ref={containerRef} className="w-full bg-card border border-border/50 rounded-2xl p-8 backdrop-blur-sm overflow-hidden">
      <h2 className="text-2xl font-bold mb-8 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
        Journey Map
      </h2>

      {/* SVG Canvas for connections */}
      <div className="relative w-full h-96 mb-8">
        <svg
          ref={svgRef}
          className="absolute inset-0 w-full h-full"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
        >
          <defs>
            <linearGradient id="pathGradient1" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="rgba(59, 130, 246, 0.6)" />
              <stop offset="100%" stopColor="rgba(34, 211, 238, 0.6)" />
            </linearGradient>
            <linearGradient id="pathGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="rgba(34, 211, 238, 0.6)" />
              <stop offset="100%" stopColor="rgba(59, 130, 246, 0.6)" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="2" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Connecting paths */}
          <path
            d="M 15 50 Q 32.5 35 50 50"
            stroke="url(#pathGradient1)"
            strokeWidth="2"
            fill="none"
            filter="url(#glow)"
          />
          <path
            d="M 50 50 Q 67.5 65 85 50"
            stroke="url(#pathGradient2)"
            strokeWidth="2"
            fill="none"
            filter="url(#glow)"
          />
        </svg>

        {/* City Nodes */}
        <div className="absolute inset-0">
          {cities.map((city, idx) => {
            const duration = travelData.itinerary[idx]?.transportation
              ? parseTransportation(travelData.itinerary[idx].transportation)
              : null

            return (
              <motion.div
                key={city.id}
                data-node
                className="absolute flex flex-col items-center transform -translate-x-1/2 -translate-y-1/2"
                style={{ left: city.x, top: city.y }}
                whileHover={{ scale: 1.15 }}
              >
                {/* Outer glow ring */}
                <div className={`absolute inset-0 rounded-full bg-gradient-to-r ${city.color} opacity-20 blur-xl animate-pulse`}
                  style={{ width: '120px', height: '120px', left: '-60px', top: '-60px' }}
                />

                {/* Main node */}
                <div
                  className={`relative w-24 h-24 rounded-full bg-gradient-to-r ${city.color} flex items-center justify-center shadow-2xl border-2 border-white/20 backdrop-blur-sm hover:shadow-cyan-500/50 hover:border-cyan-400/50 transition-all cursor-pointer`}
                >
                  <MapPin className="w-8 h-8 text-white" />
                </div>

                {/* City label */}
                <div className="mt-6 text-center">
                  <p className="font-bold text-foreground text-sm whitespace-nowrap">
                    {city.name}
                  </p>
                  {city.isReturn && (
                    <p className="text-xs text-muted-foreground">Day {travelData.days}</p>
                  )}
                </div>

                {/* Journey info below node */}
                {!city.isReturn && idx < travelData.itinerary.length && (
                  <motion.div
                    className="absolute top-full mt-12 bg-gradient-to-b from-primary/20 to-accent/10 border border-primary/30 rounded-lg p-3 backdrop-blur-sm whitespace-nowrap text-xs"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.8 + idx * 0.2 }}
                  >
                    {idx < travelData.itinerary.length - 1 && duration && (
                      <div className="flex items-center gap-2 text-cyan-400">
                        <Clock className="w-3 h-3" />
                        <span>{duration.total}</span>
                      </div>
                    )}
                    {idx === 0 && (
                      <div className="flex items-center gap-2 text-cyan-400">
                        <DollarSign className="w-3 h-3" />
                        <span>$49</span>
                      </div>
                    )}
                  </motion.div>
                )}
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Route details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {travelData.itinerary.map((leg, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2 + idx * 0.2 }}
            className="group relative overflow-hidden bg-card border border-border/20 rounded-3xl h-[220px] shadow-sm hover:shadow-md transition-all duration-500 flex flex-col justify-end"
          >
            {/* Background Image */}
            <div className="absolute inset-0 z-0 bg-muted/20">
              <img 
                src={`/travel_planner_assets/travel_planner_asset_${(idx % 6) + 1}.jpg`}
                alt={`Day ${leg.day} scenery`}
                className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110 opacity-80"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-background via-background/80 to-background/20" />
            </div>

            {/* Content Overlay */}
            <div className="relative z-10 p-6 flex flex-col gap-1">
              <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-accent">Day {leg.day}</span>
              <h3 className="font-serif text-2xl font-bold text-foreground mb-1">{leg.current_city}</h3>
              {leg.transportation !== '-' && (
                <p className="text-xs text-muted-foreground line-clamp-2 mt-1">{leg.transportation}</p>
              )}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}

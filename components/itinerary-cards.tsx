'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, MapPin, Utensils, Bed, Navigation2, Coffee } from 'lucide-react'

interface ItineraryItem {
  day: number
  current_city: string
  transportation: string
  breakfast: string
  attraction: string
  lunch: string
  dinner: string
  accommodation: string
}

interface ItineraryCardsProps {
  itinerary: ItineraryItem[]
}

export function ItineraryCards({ itinerary }: ItineraryCardsProps) {
  const [expandedDay, setExpandedDay] = useState<number | null>(null)
  const [randomAssets, setRandomAssets] = useState<Record<number, number>>({})

  // ✅ FIX: ensure safe array
  const safeItinerary = Array.isArray(itinerary) ? itinerary : [];

  const getIcon = (type: string) => {
    switch (type) {
      case 'breakfast':
        return <Coffee className="w-4 h-4" />
      case 'lunch':
      case 'dinner':
        return <Utensils className="w-4 h-4" />
      case 'attraction':
        return <MapPin className="w-4 h-4" />
      case 'accommodation':
        return <Bed className="w-4 h-4" />
      case 'transportation':
        return <Navigation2 className="w-4 h-4" />
      default:
        return null
    }
  }

  const renderDetail = (label: string, value: string, type: string) => {
    if (value === '-' || !value) return null

    return (
      <motion.div
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -10 }}
        className="flex gap-4 items-start pb-6"
      >
        <div className="text-accent mt-1 flex-shrink-0">{getIcon(type)}</div>
        <div className="flex-1 min-w-0">
          <p className="text-[10px] text-muted-foreground/80 font-bold uppercase tracking-[0.2em]">
            {label}
          </p>
          <p className="text-base text-foreground mt-1.5 break-words font-medium">{value}</p>
        </div>
      </motion.div>
    )
  }

  return (
    <div className="space-y-4">
      {itinerary.map((item, idx) => (
        <motion.div
          key={item.day}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: idx * 0.1 }}
          className="relative"
        >
          {/* Timeline line */}
          {idx < itinerary.length - 1 && (
            <div className="absolute left-[34px] top-12 w-[1px] h-10 bg-border/60" />
          )}

          {/* Card */}
          <motion.button
            onClick={() => {
              if (expandedDay === item.day) {
                setExpandedDay(null)
              } else {
                setExpandedDay(item.day)
                setRandomAssets(prev => ({
                  ...prev,
                  [item.day]: Math.floor(Math.random() * 6) + 1
                }))
              }
            }}
            className="w-full text-left"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="relative bg-card border border-border/40 rounded-2xl overflow-hidden hover:border-primary/50 transition-all group shadow-sm hover:shadow-md">
              {/* Background Image Layer */}
              <div className="absolute inset-0 z-0 pointer-events-none">
                <img
                  src={`/travel_planner_assets/travel_planner_asset_${(idx % 6) + 1}.jpg`}
                  alt={`Day ${item.day} scenery`}
                  className="absolute inset-0 w-full h-full object-cover transition-transform duration-1000 group-hover:scale-105 opacity-[0.35] dark:opacity-[0.15]"
                />
                {/* Multi-directional gradient mask for perfect text legibility */}
                <div className="absolute inset-0 bg-gradient-to-r from-card via-card/90 to-transparent z-10" />
                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-card/80 to-card z-10" />
              </div>

              {/* Accent bar */}
              <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-accent to-primary z-20" />

              <div className="relative z-20 pl-6 pr-6 py-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-5 flex-1">
                    {/* Day indicator */}
                    <div className="relative">
                      <motion.div
                        animate={{
                          scale: expandedDay === item.day ? 1.05 : 1,
                        }}
                        className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-bold text-xs border border-primary/30 shadow-sm"
                      >
                        {item.day}
                      </motion.div>
                    </div>

                    {/* Title */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-xl font-serif font-bold text-foreground">Day {item.day}</h3>
                      <p className="text-xs text-primary font-bold uppercase tracking-[0.1em] truncate mt-0.5">
                        {item.current_city}
                      </p>
                    </div>
                  </div>

                  {/* Expand indicator */}
                  <motion.div
                    animate={{ rotate: expandedDay === item.day ? 180 : 0 }}
                    transition={{ duration: 0.3 }}
                    className="text-accent flex-shrink-0 bg-accent/10 p-1.5 rounded-full"
                  >
                    <ChevronDown className="w-4 h-4" />
                  </motion.div>
                </div>
              </div>

              {/* Expanded content */}
              <AnimatePresence>
                {expandedDay === item.day && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                    className="relative z-20 border-t border-border/40 bg-card/95 backdrop-blur-md px-6 py-6"
                  >
                    <div className="flex flex-col md:flex-row gap-8 items-stretch">
                      <div className="flex-1 space-y-2">
                        {renderDetail('Transportation', item.transportation, 'transportation')}
                        {renderDetail('Breakfast', item.breakfast, 'breakfast')}
                        {renderDetail('Lunch', item.lunch, 'lunch')}
                        {renderDetail('Dinner', item.dinner, 'dinner')}
                        {renderDetail('Attractions', item.attraction, 'attraction')}
                        {renderDetail('Accommodation', item.accommodation, 'accommodation')}
                      </div>

                      {/* Randomly Selected Asset Box on the Right */}
                      {randomAssets[item.day] && (
                        <motion.div 
                          initial={{ opacity: 0, scale: 0.95 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ duration: 0.4, delay: 0.2 }}
                          className="w-full md:w-2/5 lg:w-[45%] rounded-2xl overflow-hidden shadow-sm relative flex-shrink-0 group-hover:shadow-md transition-shadow ring-1 ring-border/50 min-h-[220px]"
                        >
                          <img 
                            src={`/itienerary_assets/itinerary_asset_${randomAssets[item.day]}.png`}
                            alt={`Day ${item.day} showcase`}
                            className="absolute inset-0 w-full h-full object-cover transition-transform duration-1000 group-hover:scale-105"
                          />
                        </motion.div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.button>
        </motion.div>
      ))}
    </div>
  )
}

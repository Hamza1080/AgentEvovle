'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { DayPicker, DateRange } from 'react-day-picker'
import 'react-day-picker/style.css'

// ─── Types ────────────────────────────────────────────────────────────────────
interface TripFormData {
  origin: string
  destination: string
  query: string
  dateRange: DateRange | undefined
  travelers: number
  budget: string
  roomType: string
  houseRules: string[]
  cuisines: string[]
  masStrategy: 'budget' | 'experience'
}

interface InputScreenProps {
  onSubmit: (data: TripFormData) => void
}

// ─── City data ─────────────────────────────────────────────────────────────────
const CITIES = [
  { name: 'Provo', state: 'UT' },
  { name: 'Phoenix', state: 'AZ' },
  { name: 'New York City', state: 'NY' },
  { name: 'Los Angeles', state: 'CA' },
  { name: 'Seattle', state: 'WA' },
  { name: 'Portland', state: 'OR' },
  { name: 'San Francisco', state: 'CA' },
  { name: 'Boston', state: 'MA' },
  { name: 'Chicago', state: 'IL' },
  { name: 'Austin', state: 'TX' },
  { name: 'Las Vegas', state: 'NV' },
  { name: 'Washington D.C.', state: 'DC' },
  { name: 'Miami', state: 'FL' },
  { name: 'Salt Lake City', state: 'UT' },
  { name: 'Atlanta', state: 'GA' },
  { name: 'Denver', state: 'CO' },
  { name: 'Nashville', state: 'TN' },
  { name: 'San Diego', state: 'CA' },
  { name: 'Dallas', state: 'TX' },
  { name: 'Minneapolis', state: 'MN' },
]

const ROOM_TYPES = ['Private Room', 'Entire Home', 'Hotel Room', 'Hostel Dorm']

const HOUSE_RULES = [
  { id: 'pets', label: 'Pets Allowed' },
  { id: 'no-smoking', label: 'No Smoking' },
  { id: 'self-checkin', label: 'Self Check-in' },
  { id: 'accessible', label: 'Wheelchair Accessible' },
]

const CUISINES = [
  'Italian', 'Indian', 'French', 'Japanese', 'Mexican',
  'American', 'Mediterranean', 'Thai', 'Chinese', 'Korean',
]

// ─── Sub-components ────────────────────────────────────────────────────────────

function SectionLabel({ index, children }: { index: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      <span className="text-[10px] font-bold tracking-[0.25em] text-[#8CA090] uppercase">{index}</span>
      <div className="h-px flex-1 bg-[#313A43]" />
      <h2 className="text-xs font-semibold uppercase tracking-[0.2em] text-[#9CA3AF]">{children}</h2>
    </div>
  )
}

function CityCard({
  city,
  isSelected,
  role,
  onClick,
}: {
  city: { name: string; state: string }
  isSelected: 'origin' | 'destination' | null
  role: 'origin' | 'destination' | null
  onClick: () => void
}) {
  const isActive = isSelected !== null
  const borderColor = isSelected === 'origin'
    ? 'border-[#8CA090]'
    : isSelected === 'destination'
    ? 'border-[#6B8FA0]'
    : 'border-[#313A43]'
  const bgColor = isSelected === 'origin'
    ? 'bg-[#8CA090]/10'
    : isSelected === 'destination'
    ? 'bg-[#6B8FA0]/10'
    : 'bg-[#1C2126] hover:bg-[#24292D]'

  return (
    <motion.button
      onClick={onClick}
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      className={`relative flex-shrink-0 w-28 h-20 rounded-2xl border ${borderColor} ${bgColor} flex flex-col items-start justify-end p-3 cursor-pointer transition-all duration-200 group overflow-hidden`}
    >
      {isSelected && (
        <motion.div
          layoutId={`badge-${isSelected}`}
          className={`absolute top-2 right-2 text-[8px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded-md ${
            isSelected === 'origin' ? 'bg-[#8CA090] text-[#121619]' : 'bg-[#6B8FA0] text-[#121619]'
          }`}
        >
          {isSelected === 'origin' ? 'From' : 'To'}
        </motion.div>
      )}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
        <div className={`absolute inset-0 opacity-5 bg-gradient-to-br ${
          isSelected === 'origin' ? 'from-[#8CA090]' :
          isSelected === 'destination' ? 'from-[#6B8FA0]' :
          'from-transparent'
        } to-transparent`} />
      </div>
      <span className="text-[9px] font-bold tracking-widest text-[#9CA3AF] uppercase">{city.state}</span>
      <span className="text-sm font-semibold text-[#F9F9F7] leading-tight mt-0.5">{city.name}</span>
    </motion.button>
  )
}

function Counter({ value, onChange, min = 1, max = 12 }: {
  value: number
  onChange: (v: number) => void
  min?: number
  max?: number
}) {
  return (
    <div className="flex items-center gap-4">
      <button
        onClick={() => onChange(Math.max(min, value - 1))}
        disabled={value <= min}
        className="w-9 h-9 rounded-xl border border-[#313A43] bg-[#1C2126] text-[#F9F9F7] flex items-center justify-center text-lg font-light hover:border-[#8CA090] hover:bg-[#8CA090]/10 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
      >−</button>
      <motion.span
        key={value}
        initial={{ y: -8, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="text-3xl font-bold text-[#F9F9F7] w-10 text-center tabular-nums"
      >
        {value}
      </motion.span>
      <button
        onClick={() => onChange(Math.min(max, value + 1))}
        disabled={value >= max}
        className="w-9 h-9 rounded-xl border border-[#313A43] bg-[#1C2126] text-[#F9F9F7] flex items-center justify-center text-lg font-light hover:border-[#8CA090] hover:bg-[#8CA090]/10 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
      >+</button>
      <span className="text-sm text-[#9CA3AF] ml-1">
        {value === 1 ? 'traveler' : 'travelers'}
      </span>
    </div>
  )
}

function CustomCheckbox({ checked, onChange, label }: {
  checked: boolean
  onChange: () => void
  label: string
}) {
  return (
    <button
      onClick={onChange}
      className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-all duration-200 ${
        checked
          ? 'border-[#8CA090] bg-[#8CA090]/10'
          : 'border-[#313A43] bg-[#1C2126] hover:border-[#4A5D4E]'
      }`}
    >
      <div className={`w-4 h-4 rounded-md border-2 flex items-center justify-center transition-all ${
        checked ? 'border-[#8CA090] bg-[#8CA090]' : 'border-[#4A5560]'
      }`}>
        {checked && (
          <motion.svg
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            viewBox="0 0 10 8" fill="none" className="w-2.5 h-2"
          >
            <path d="M1 4L3.5 6.5L9 1" stroke="#121619" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </motion.svg>
        )}
      </div>
      <span className={`text-sm font-medium ${checked ? 'text-[#F9F9F7]' : 'text-[#9CA3AF]'}`}>{label}</span>
    </button>
  )
}

function CuisinePill({ label, selected, onToggle }: {
  label: string
  selected: boolean
  onToggle: () => void
}) {
  return (
    <motion.button
      layout
      onClick={onToggle}
      whileTap={{ scale: 0.95 }}
      className={`px-4 py-2 rounded-full text-sm font-medium border transition-all duration-200 ${
        selected
          ? 'bg-[#8CA090] border-[#8CA090] text-[#121619]'
          : 'bg-transparent border-[#313A43] text-[#9CA3AF] hover:border-[#8CA090] hover:text-[#F9F9F7]'
      }`}
    >
      {selected && (
        <span className="mr-1.5">×</span>
      )}
      {label}
    </motion.button>
  )
}

function MASToggle({ value, onChange }: {
  value: 'budget' | 'experience'
  onChange: (v: 'budget' | 'experience') => void
}) {
  return (
    <div className="flex items-center gap-1 bg-[#1C2126] border border-[#313A43] rounded-2xl p-1.5">
      {(['budget', 'experience'] as const).map((option) => (
        <button
          key={option}
          onClick={() => onChange(option)}
          className="relative flex-1 px-5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-300 z-10"
        >
          {value === option && (
            <motion.div
              layoutId="mas-pill"
              className="absolute inset-0 rounded-xl bg-[#8CA090]"
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            />
          )}
          <span className={`relative z-10 ${
            value === option ? 'text-[#121619]' : 'text-[#9CA3AF]'
          }`}>
            {option === 'budget' ? '💰 Budget First' : '✨ Experience First'}
          </span>
        </button>
      ))}
    </div>
  )
}

// ─── Main Component ────────────────────────────────────────────────────────────

export function InputScreen({ onSubmit }: InputScreenProps) {
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [citySelectMode, setCitySelectMode] = useState<'origin' | 'destination'>('origin')
  const [query, setQuery] = useState('')
  const [dateRange, setDateRange] = useState<DateRange | undefined>()
  const [travelers, setTravelers] = useState(2)
  const [budget, setBudget] = useState('')
  const [roomType, setRoomType] = useState('Private Room')
  const [houseRules, setHouseRules] = useState<string[]>([])
  const [cuisines, setCuisines] = useState<string[]>([])
  const [masStrategy, setMasStrategy] = useState<'budget' | 'experience'>('experience')
  const [showCalendar, setShowCalendar] = useState(false)

  function getCityRole(cityName: string): 'origin' | 'destination' | null {
    if (origin === cityName) return 'origin'
    if (destination === cityName) return 'destination'
    return null
  }

  function handleCityClick(cityName: string) {
    if (origin === cityName) {
      setOrigin('')
      if (citySelectMode === 'destination') setCitySelectMode('origin')
      return
    }
    if (destination === cityName) {
      setDestination('')
      return
    }
    if (citySelectMode === 'origin') {
      setOrigin(cityName)
      setCitySelectMode('destination')
    } else {
      if (cityName !== origin) {
        setDestination(cityName)
        setCitySelectMode('origin')
      }
    }
  }

  function toggleHouseRule(id: string) {
    setHouseRules(prev =>
      prev.includes(id) ? prev.filter(r => r !== id) : [...prev, id]
    )
  }

  function toggleCuisine(name: string) {
    setCuisines(prev =>
      prev.includes(name) ? prev.filter(c => c !== name) : [...prev, name]
    )
  }

  function formatDateDisplay(range: DateRange | undefined) {
    if (!range?.from) return 'Select dates'
    const fmt = (d: Date) => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    if (!range.to) return fmt(range.from)
    return `${fmt(range.from)} – ${fmt(range.to)}`
  }

  const canSubmit = origin && destination && origin !== destination

  function handleSubmit() {
    if (!canSubmit) return
    onSubmit({
      origin, destination, query, dateRange,
      travelers, budget, roomType, houseRules,
      cuisines, masStrategy,
    })
  }

  return (
    <div className="min-h-screen bg-[#121619] text-[#F9F9F7]" style={{ fontFamily: 'Inter, SF Pro Display, system-ui, sans-serif' }}>
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl border-b border-[#313A43]/60 bg-[#121619]/85">
        <div className="max-w-5xl mx-auto px-6 lg:px-8 py-5 flex justify-between items-center">
          <div>
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-[#8CA090] to-[#6B8FA0] flex items-center justify-center">
                <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4">
                  <circle cx="8" cy="8" r="6" stroke="#121619" strokeWidth="1.5"/>
                  <path d="M8 4v4l2.5 2" stroke="#121619" strokeWidth="1.3" strokeLinecap="round"/>
                </svg>
              </div>
              <h1 className="text-xl font-bold tracking-tight text-[#F9F9F7]">EvoAgent</h1>
            </div>
            <p className="text-[11px] text-[#9CA3AF] mt-0.5 tracking-wide">AI Travel Planner · Multi-Agent System</p>
          </div>
          <div className="flex items-center gap-2 text-[11px] text-[#9CA3AF] bg-[#1C2126] border border-[#313A43] rounded-xl px-3 py-2">
            <span className="w-1.5 h-1.5 rounded-full bg-[#8CA090] animate-pulse" />
            MAS Ready
          </div>
        </div>
      </header>

      <div className="max-w-5xl mx-auto px-6 lg:px-8 py-10 space-y-12">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="space-y-2"
        >
          <h2 className="text-4xl font-bold tracking-tight text-[#F9F9F7]">
            Plan your next{' '}
            <span className="bg-gradient-to-r from-[#8CA090] to-[#6B8FA0] bg-clip-text text-transparent">
              adventure.
            </span>
          </h2>
          <p className="text-[#9CA3AF] text-base max-w-lg">
            Our multi-agent system will craft a personalized itinerary tailored to your preferences and budget.
          </p>
        </motion.div>

        {/* Section 01 — Where & When */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="space-y-6"
        >
          <SectionLabel index="01">Where & When</SectionLabel>

          {/* City selection mode indicator */}
          <div className="flex items-center gap-3">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-medium transition-colors ${
              citySelectMode === 'origin'
                ? 'border-[#8CA090] bg-[#8CA090]/10 text-[#8CA090]'
                : 'border-[#313A43] text-[#9CA3AF]'
            }`}>
              <span>Origin</span>
              {origin && <span className="font-bold text-[#F9F9F7]">· {origin}</span>}
              {!origin && <span className="text-[10px] tracking-widest opacity-60">← SELECT</span>}
            </div>
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="w-4 h-4 text-[#4A5560]">
              <path d="M5 12h14M13 6l6 6-6 6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-medium transition-colors ${
              citySelectMode === 'destination'
                ? 'border-[#6B8FA0] bg-[#6B8FA0]/10 text-[#6B8FA0]'
                : 'border-[#313A43] text-[#9CA3AF]'
            }`}>
              <span>Destination</span>
              {destination && <span className="font-bold text-[#F9F9F7]">· {destination}</span>}
              {!destination && <span className="text-[10px] tracking-widest opacity-60">← SELECT</span>}
            </div>
          </div>

          {/* City cards */}
          <div className="relative">
            <div className="flex gap-3 overflow-x-auto pb-3 scrollbar-hide" style={{ scrollbarWidth: 'none' }}>
              {CITIES.map((city) => (
                <CityCard
                  key={city.name}
                  city={city}
                  isSelected={getCityRole(city.name)}
                  role={getCityRole(city.name)}
                  onClick={() => handleCityClick(city.name)}
                />
              ))}
            </div>
            <div className="absolute right-0 top-0 bottom-3 w-12 pointer-events-none bg-gradient-to-l from-[#121619] to-transparent" />
          </div>

          {/* Date Range */}
          <div className="relative">
            <button
              onClick={() => setShowCalendar(!showCalendar)}
              className="w-full flex items-center justify-between px-5 py-4 bg-[#1C2126] border border-[#313A43] rounded-2xl hover:border-[#8CA090]/50 transition-all group"
            >
              <div className="flex items-center gap-3">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="w-5 h-5 text-[#8CA090]">
                  <rect x="3" y="4" width="18" height="18" rx="3" strokeWidth="1.5"/>
                  <path d="M3 9h18M8 2v4M16 2v4" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
                <span className={`text-sm font-medium ${dateRange?.from ? 'text-[#F9F9F7]' : 'text-[#6A7175]'}`}>
                  {formatDateDisplay(dateRange)}
                </span>
              </div>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                className={`w-4 h-4 text-[#9CA3AF] transition-transform ${showCalendar ? 'rotate-180' : ''}`}
              >
                <path d="M6 9l6 6 6-6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>

            <AnimatePresence>
              {showCalendar && (
                <motion.div
                  initial={{ opacity: 0, y: -8, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.98 }}
                  transition={{ duration: 0.2 }}
                  className="absolute top-full left-0 mt-2 z-50 bg-[#1C2126] border border-[#313A43] rounded-2xl shadow-2xl p-4"
                >
                  <style>{`
                    .rdp { --rdp-accent-color: #8CA090; --rdp-background-color: #8CA090; color: #F9F9F7; }
                    .rdp-day_selected, .rdp-day_selected:hover { background-color: #8CA090; color: #121619; border-radius: 8px; }
                    .rdp-day_range_middle { background-color: rgba(140,160,144,0.2); color: #F9F9F7; }
                    .rdp-day_range_end, .rdp-day_range_start { background-color: #8CA090; color: #121619; border-radius: 8px; }
                    .rdp-caption_label { color: #F9F9F7; font-size: 13px; font-weight: 600; }
                    .rdp-nav_button { color: #9CA3AF; }
                    .rdp-nav_button:hover { background-color: #24292D; }
                    .rdp-head_cell { color: #6A7175; font-size: 11px; font-weight: 600; letter-spacing: 0.1em; }
                    .rdp-day { color: #D1D5DB; font-size: 13px; border-radius: 8px; }
                    .rdp-day:hover:not(.rdp-day_selected) { background-color: #24292D; }
                    .rdp-day_outside { color: #4A5560; }
                  `}</style>
                  <DayPicker
                    mode="range"
                    selected={dateRange}
                    onSelect={(range) => {
                      setDateRange(range)
                      if (range?.to) setShowCalendar(false)
                    }}
                    numberOfMonths={2}
                    disabled={{ before: new Date() }}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.section>

        {/* Section 02 — Trip Description */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="space-y-4"
        >
          <SectionLabel index="02">Trip Description</SectionLabel>
          <div className="relative">
            <textarea
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Describe your ideal trip vibe... e.g. 'Looking for a quiet, nature-focused getaway with light hiking and good local food.'"
              rows={4}
              className="w-full bg-[#1C2126] border border-[#313A43] rounded-2xl px-5 py-4 text-sm text-[#F9F9F7] placeholder-[#4A5560] resize-none focus:outline-none focus:border-[#8CA090]/60 transition-colors"
            />
            <div className="absolute bottom-4 right-4 text-[11px] text-[#4A5560] tabular-nums">
              {query.length}/500
            </div>
          </div>
        </motion.section>

        {/* Section 03 — Who & How Much */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="space-y-6"
        >
          <SectionLabel index="03">Who & How Much</SectionLabel>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Travelers */}
            <div className="bg-[#1A2020] border border-[#313A43] rounded-2xl p-6 space-y-3">
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[#9CA3AF]">Travelers</p>
              <Counter value={travelers} onChange={setTravelers} />
            </div>
            {/* Budget */}
            <div className="bg-[#1A2020] border border-[#313A43] rounded-2xl p-6 space-y-3">
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[#9CA3AF]">Total Budget</p>
              <div className="flex items-center gap-2 bg-[#121619] border border-[#313A43] rounded-xl px-4 py-3 focus-within:border-[#8CA090]/60 transition-colors">
                <span className="text-[#8CA090] text-base font-bold">$</span>
                <input
                  type="number"
                  value={budget}
                  onChange={e => setBudget(e.target.value)}
                  placeholder="2,500"
                  className="flex-1 bg-transparent text-base font-semibold text-[#F9F9F7] placeholder-[#4A5560] focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                />
                <span className="text-[11px] text-[#4A5560] font-medium">USD</span>
              </div>
            </div>
          </div>
        </motion.section>

        {/* Section 04 — Accommodation */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="space-y-6"
        >
          <SectionLabel index="04">Accommodation</SectionLabel>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Room Type */}
            <div className="space-y-2">
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[#9CA3AF]">Room Type</p>
              <div className="relative">
                <select
                  value={roomType}
                  onChange={e => setRoomType(e.target.value)}
                  className="w-full appearance-none bg-[#1C2126] border border-[#313A43] rounded-2xl px-5 py-4 pr-10 text-sm font-medium text-[#F9F9F7] focus:outline-none focus:border-[#8CA090]/60 transition-colors cursor-pointer"
                  style={{ backgroundImage: 'none' }}
                >
                  {ROOM_TYPES.map(rt => (
                    <option key={rt} value={rt} className="bg-[#1C2126]">{rt}</option>
                  ))}
                </select>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF] pointer-events-none"
                >
                  <path d="M6 9l6 6 6-6" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </div>

            {/* House Rules */}
            <div className="space-y-2">
              <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-[#9CA3AF]">House Rules</p>
              <div className="grid grid-cols-2 gap-2">
                {HOUSE_RULES.map(rule => (
                  <CustomCheckbox
                    key={rule.id}
                    checked={houseRules.includes(rule.id)}
                    onChange={() => toggleHouseRule(rule.id)}
                    label={rule.label}
                  />
                ))}
              </div>
            </div>
          </div>
        </motion.section>

        {/* Section 05 — Cuisine Preferences */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="space-y-4"
        >
          <SectionLabel index="05">Cuisine Preferences</SectionLabel>
          <div className="flex flex-wrap gap-2">
            {CUISINES.map(cuisine => (
              <CuisinePill
                key={cuisine}
                label={cuisine}
                selected={cuisines.includes(cuisine)}
                onToggle={() => toggleCuisine(cuisine)}
              />
            ))}
          </div>
          {cuisines.length > 0 && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-[11px] text-[#8CA090] tracking-wide"
            >
              {cuisines.length} cuisine{cuisines.length > 1 ? 's' : ''} selected: {cuisines.join(' · ')}
            </motion.p>
          )}
        </motion.section>

        {/* Section 06 — MAS Planning Strategy */}
        <motion.section
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="space-y-4"
        >
          <SectionLabel index="06">Planning Strategy</SectionLabel>
          <div className="bg-[#1A2020] border border-[#313A43] rounded-2xl p-5 space-y-4">
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#8CA090]/10 border border-[#8CA090]/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <svg viewBox="0 0 16 16" fill="none" className="w-4 h-4">
                  <path d="M8 1l1.5 4.5H14l-3.5 2.5 1 4L8 9.5 4.5 12l1-4L2 5.5h4.5L8 1z" stroke="#8CA090" strokeWidth="1.2" strokeLinejoin="round"/>
                </svg>
              </div>
              <div>
                <p className="text-sm font-semibold text-[#F9F9F7]">MAS Expert Agent Weighting</p>
                <p className="text-[11px] text-[#6A7175] mt-0.5 leading-relaxed">
                  Controls how our multi-agent system prioritizes trade-offs when crafting your itinerary.
                </p>
              </div>
            </div>
            <MASToggle value={masStrategy} onChange={setMasStrategy} />
          </div>
        </motion.section>

        {/* Submit */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="pb-12"
        >
          <motion.button
            onClick={handleSubmit}
            disabled={!canSubmit}
            whileHover={canSubmit ? { scale: 1.015 } : {}}
            whileTap={canSubmit ? { scale: 0.985 } : {}}
            className={`relative w-full py-5 rounded-2xl text-base font-bold tracking-wide transition-all duration-300 overflow-hidden ${
              canSubmit
                ? 'bg-gradient-to-r from-[#4A5D4E] to-[#3D5A60] text-[#F9F9F7] hover:from-[#5A7060] hover:to-[#4A6A72] cursor-pointer'
                : 'bg-[#1C2126] text-[#4A5560] border border-[#313A43] cursor-not-allowed'
            }`}
          >
            {canSubmit && (
              <div className="absolute inset-0 pointer-events-none">
                <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[#8CA090]/30 to-transparent" />
                <div className="absolute inset-0 bg-gradient-to-r from-[#8CA090]/0 via-[#8CA090]/5 to-[#6B8FA0]/0" />
              </div>
            )}
            <span className="relative flex items-center justify-center gap-3">
              {canSubmit ? (
                <>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="w-5 h-5">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" strokeWidth="1.5"/>
                    <path d="M8 12h8M13 9l3 3-3 3" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  Generate Itinerary with AI Agents
                </>
              ) : (
                'Select origin & destination to continue'
              )}
            </span>
          </motion.button>

          {canSubmit && (
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-center text-[11px] text-[#6A7175] mt-3"
            >
              Our multi-agent system will take 3–4 minutes to craft your optimal itinerary
            </motion.p>
          )}
        </motion.div>
      </div>
    </div>
  )
}

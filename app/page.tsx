'use client'

import dynamic from 'next/dynamic'
import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import gsap from 'gsap'
import { ItineraryCards } from '@/components/itinerary-cards'
import { ThemeToggle } from '@/components/theme-toggle'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { NoiseBackground } from '@/components/ui/noise-background'
import { InputScreen } from '@/components/input-screen'
import { LoadingScreen } from '@/components/loading-screen'

const TravelGlobe = dynamic(() => import('@/components/travel-globe'), {
  loading: () => (
    <div className="w-full h-96 flex items-center justify-center bg-card/50 rounded-lg border border-border/50">
      <div className="flex flex-col items-center gap-4">
        <Spinner />
        <p className="text-sm text-muted-foreground">Loading 3D globe...</p>
      </div>
    </div>
  ),
  ssr: false,
})

type AppView = 'input' | 'loading' | 'results'

interface TripFormData {
  origin: string
  destination: string
  query: string
  dateRange: unknown
  travelers: number
  budget: string
  roomType: string
  houseRules: string[]
  cuisines: string[]
  masStrategy: 'budget' | 'experience'
}

export default function Home() {
  const [view, setView] = useState<AppView>('input')   // uncomment 2
  // const [view, setView] = useState<AppView>('results')  //comment 1
  const [formData, setFormData] = useState<TripFormData | null>(null)
  const [showDetails, setShowDetails] = useState(false)
  const [travelData, setTravelData] = useState<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  // uncomment

  // Fetch travel data for the results view (pre-fetch in background) 
  // useEffect(() => {
  //   fetch('/api/travel-data')
  //     .then(res => res.json())
  //     .then(data => setTravelData(data))
  //     .catch(err => console.error("Could not fetch travel data", err))
  // }, [])

    //   useEffect(() => {
    //   console.log("🚫 travel-data API disabled (migration step 1)");

    //   // TEMP MOCK (so UI doesn't crash)
    //   const mockData = {
    //     org: "St. Petersburg",
    //     dest: "Rockford",
    //     days: 3,
    //     people_number: 1,
    //     budget: 1700,
    //     itinerary: []
    //   };

    //   setTravelData(mockData);
    // }, []);

  // //delete start
  //     useEffect(() => {
  //     const mockData = {
  //       org: "New York",
  //       dest: "Los Angeles",
  //       days: 5,
  //       people_number: 2,
  //       budget: 2500,
  //       itinerary: [
  //         {
  //           day: 1,
  //           current_city: "New York",
  //           transportation: "-",
  //           breakfast: "Hotel breakfast",
  //           attraction: "Statue of Liberty",
  //           lunch: "Local cafe",
  //           dinner: "Times Square dinner",
  //           accommodation: "NY Hotel"
  //         },
  //         {
  //           day: 2,
  //           current_city: "Los Angeles",
  //           transportation: "Flight to LA",
  //           breakfast: "Airport coffee",
  //           attraction: "Hollywood Sign",
  //           lunch: "In-N-Out",
  //           dinner: "Santa Monica",
  //           accommodation: "LA Hotel"
  //         }
  //       ]
  //     }

  //     console.log("USING MOCK DATA:", mockData)
  //     setTravelData(mockData)
  //   }, [])
  //delete end


  useEffect(() => {
    if (travelData && containerRef.current && view === 'results') {
      gsap.fromTo(
        containerRef.current,
        { opacity: 0, y: 20 },
        { opacity: 1, y: 0, duration: 0.8, ease: 'power3.out' }
      )
    }
  }, [travelData, view])

//   async function handleFormSubmit(data: TripFormData) {
//   setFormData(data);
//   setView('loading');

//   try {
//     console.log("🚀 Sending to /api/plan:", data);

//     const res = await fetch("/api/plan", {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//       },
//       body: JSON.stringify(data),
//     });

//     const result = await res.json();

//     console.log("📦 API RESPONSE:", result);

//     // optional: you can check if saved successfully
//     if (!result.success) {
//       throw new Error(result.error || "Save failed");
//     }

//   } catch (err) {
//     console.error("❌ PLAN ERROR:", err);
//   }
// }


  async function handleFormSubmit(data: TripFormData) {
    setFormData(data);
    setView("loading");

    try {
      await fetch("/api/plan", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      const res = await fetch("/api/run-model", {
        method: "POST",
      });

      const result = await res.json();
      console.log("MODEL RESULT:", result);

      if (!result.success) {
        throw new Error(result.error);
      }

      // ✅ IMPORTANT FIX: correct source
      const output = result.normalized || result.data || result.output;

      const safeData = {
        org: output?.org ?? data.origin ?? "Unknown",
        dest: output?.dest ?? data.destination ?? "Unknown",
        days: output?.days ?? 1,
        people_number: output?.people_number ?? data.travelers ?? 1,
        budget: output?.budget ?? 0,
        itinerary: Array.isArray(output?.itinerary) ? output.itinerary : [],
      };

      console.log("SETTING SAFE DATA:", safeData);

      setTravelData(safeData);
      setView("results");

    } catch (err) {
      console.error("PIPELINE ERROR:", err);
      setView("input");
    }
  }
  // ── Input view ───────────────────────────────────────────────────────────────
  if (view === 'input') {
    return <InputScreen onSubmit={handleFormSubmit} />
  }
  
  function handleLoadingComplete() {
  setView("results");
}

  // ── Loading view ─────────────────────────────────────────────────────────────
  if (view === 'loading') {
    return (
      <LoadingScreen
        tripDetails={formData ? {
          origin: formData.origin,
          destination: formData.destination,
          travelers: formData.travelers,
          masStrategy: formData.masStrategy,
        } : undefined}
        onComplete={handleLoadingComplete}
      />
    )
  }

  // ── Results view ─────────────────────────────────────────────────────────────
  if (!travelData) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
        <Spinner />
        <p className="mt-4 text-muted-foreground animate-pulse">Loading journey data...</p>
      </div>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-background/95 text-foreground">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-md border-b border-border/50 bg-background/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Travel Plan
            </h1>
            <p className="text-sm text-muted-foreground mt-1">Interactive Journey Visualization</p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setView('input')}
              className="border-border/40 bg-transparent hover:bg-muted/50 text-foreground text-xs"
            >
              ← New Plan
            </Button>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <div ref={containerRef} className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
        {/* Bento grid flow */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="grid gap-4 lg:grid-cols-12 auto-rows-[minmax(120px,auto)]"
        >
          {/* Globe - oversized */}
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.25 }}
            className="lg:col-span-8 lg:row-span-4 col-span-12"
          >
            <NoiseBackground
              containerClassName="rounded-3xl border border-border/60 h-full min-h-[500px]"
              className="h-full"
              gradientColors={[
                'rgb(93, 170, 255)',
                'rgb(56, 189, 248)',
                'rgb(132, 94, 247)',
              ]}
              noiseIntensity={0.12}
            >
              <div className="h-full overflow-hidden rounded-2xl border border-white/5">
                <TravelGlobe
                origin={travelData?.org ?? "New York"}
                destination={travelData?.dest ?? "Los Angeles"}
              />
              </div>
            </NoiseBackground>
          </motion.div>

          {/* Stats Grid */}
          {[
            { label: 'Origin', value: formData?.origin || travelData.org },
            { label: 'Destination', value: formData?.destination || travelData.dest },
            { label: 'Duration', value: `${travelData.days} days` },
            { label: 'Travelers', value: `${formData?.travelers || travelData.people_number} people` },
          ].map((stat, idx) => (
            <motion.div
              key={stat.label}
              whileHover={{ scale: 1.03 }}
              className="lg:col-span-2 lg:row-span-1 col-span-6 bg-card/30 border border-border/20 rounded-3xl p-5 backdrop-blur-md hover:bg-card/50 transition-all relative overflow-hidden flex flex-col justify-center"
            >
              <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent">0{idx + 1}</span>
              <p className="text-[10px] text-muted-foreground/80 font-bold uppercase tracking-[0.2em] mt-2">
                {stat.label}
              </p>
              <p className="text-lg font-bold text-foreground mt-2">{stat.value}</p>
              <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/5 to-accent/5" />
            </motion.div>
          ))}

          {/* Budget Overview */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-4 lg:row-span-2 col-span-12 flex flex-col"
          >
            <NoiseBackground
              containerClassName="rounded-3xl border border-border/60 h-full flex-1"
              className="p-6 md:p-7 flex flex-col justify-between"
              gradientColors={[
                'rgb(132, 94, 247)',
                'rgb(56, 189, 248)',
                'rgb(93, 170, 255)',
              ]}
              noiseIntensity={0.1}
            >
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-accent">05</span>
                  <h2 className="text-xl font-serif font-bold mt-2 text-foreground">Budget Overview</h2>
                </div>
                <span className="text-sm text-muted-foreground">USD</span>
              </div>
              <div className="space-y-3 mt-4">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground/80">Total Budget</span>
                  <span className="text-2xl font-bold text-accent">
                    ${formData?.budget || travelData.budget}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground/80">Transportation</span>
                  <span className="text-lg font-semibold text-primary">$98 (7%)</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground/80">Accommodation</span>
                  <span className="text-lg font-semibold text-primary">$540 (39%)</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground/80">Food & Dining</span>
                  <span className="text-lg font-semibold text-primary">$450 (32%)</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-muted-foreground/80">Activities & Attractions</span>
                  <span className="text-lg font-semibold text-primary">$312 (22%)</span>
                </div>
              </div>
            </NoiseBackground>
          </motion.div>
        </motion.div>

        {/* Itinerary Toggle */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="flex justify-center"
        >
          <Button
            onClick={() => setShowDetails(!showDetails)}
            variant="outline"
            className="border-border/40 bg-transparent hover:bg-muted/50 text-foreground"
            size="lg"
          >
            {showDetails ? 'Hide' : 'Show'} Day-by-Day Itinerary
          </Button>
        </motion.div>

        {/* Detailed Itinerary */}
        {showDetails && travelData?.itinerary?.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.4 }}
          >
            <ItineraryCards itinerary={travelData?.itinerary ?? []} />
          </motion.div>
        )}

        {/* Footer */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6 }}
          className="text-center py-8 border-t border-border/50"
        >
          <p className="text-muted-foreground text-sm">
            Travel Plan for {formData?.travelers || travelData.people_number} travelers · Generated by EvoAgent MAS
          </p>
        </motion.div>
      </div>
    </main>
  )
}

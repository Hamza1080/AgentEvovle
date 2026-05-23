# Travel Planner Visual

Demo Video
https://www.loom.com/share/892883a5503d401d805a6d25d3a88109

A [Next.js](https://nextjs.org/) app that turns a trip intake form into an **interactive results dashboard**: a 3D globe between origin and destination, trip stats, a budget-style summary, and an expandable day-by-day itinerary. It is built as a **visualization front end** for EvoAgent-style multi-agent travel planning, with itinerary data served from local JSON for demos and prototyping.

## Features

- **Three-step flow**: trip preferences → animated loading screen → results dashboard
- **3D globe** ([React Three Fiber](https://docs.pmnd.rs/react-three-fiber/)) with markers for origin/destination (coordinates from `data/uscities.json`; marker art via [DiceBear](https://www.dicebear.com/))
- **Results layout**: bento-style grid with [Framer Motion](https://www.framer.com/motion/) and [GSAP](https://gsap.com/) entrance animation
- **Day-by-day itinerary** cards driven by mock API data
- **Dark/light themes** via [next-themes](https://github.com/pacocoursey/next-themes)
- **[Vercel Analytics](https://vercel.com/docs/analytics)** in the root layout (optional in production)

## Tech stack

| Area | Choice |
|------|--------|
| Framework | Next.js 16 (App Router) |
| UI | React 19, Tailwind CSS 4, Radix-based UI primitives (shadcn-style) |
| 3D | `three`, `@react-three/fiber`, `@react-three/drei` |
| Motion | Framer Motion, GSAP |
| Forms / validation | React Hook Form, Zod, `@hookform/resolvers` |

## Prerequisites

- [Node.js](https://nodejs.org/) 20+ (recommended for current Next.js releases)
- [Python](https://www.python.org/) 3.12+ (for the EvoAgent backend)
- [pnpm](https://pnpm.io/) (recommended) or npm

## Environment Setup

### Frontend (Next.js)

Copy the example env file and fill in your key:

```bash
cp .env.example .env.local
```

Edit `.env.local`:
```env
OPENAI_API_KEY=sk-...your-key...
```

### Python Backend

```bash
cd app/api/run-model/agents
cp .env.example .env
# Then edit .env with your API keys and paths
```

Install Python dependencies (use a virtual environment):
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

## Getting started

Install Node dependencies (the repo uses pnpm as its primary package manager):

```bash
pnpm install
# or: npm install
```

Run the development server:

```bash
pnpm dev
# or: npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Submit the form to move through loading, then the results view.

Other scripts:

```bash
pnpm build    # production build
pnpm start    # run production server (after build)
```

`package.json` also defines `lint` (`eslint .`), but **ESLint is not installed** in this repo yet. Add `eslint` and a config if you want that script to work.

## How data flows (current demo)

1. On load, the home page fetches **`GET /api/travel-data`** once.
2. `app/api/travel-data/route.ts` returns a **random** trip from `data/mock-travel-data.json` (`Cache-Control: no-store`).
3. The **globe** reads `org` and `dest` from that payload. **Stats and itinerary** use the same object. The **total budget** line prefers the value from the form when the user entered one, otherwise `budget` from JSON.
4. **Important:** The trip **form is not sent to any backend** today. `LoadingScreen` is a **timed animation** (~3.5 minutes) and does not wait on your engine. Connecting a real multi-agent system means changing this flow (see below).

## Integrating a multi-agent travel planner backend

This UI is meant to sit in front of an **orchestrated planner** (multi-agent LLM workflow, constraint solver + tools, LangGraph/CrewAI/AutoGen-style system, or a custom microservice). The mock JSON is a **contract sketch**: your backend should produce JSON the app can render, or you add a thin **adapter** in Next.js.

### 1. Decide where the engine runs

| Approach | When to use | Notes |
|----------|-------------|--------|
| **Next.js API route as BFF** (recommended) | Engine is HTTP/gRPC elsewhere, or you need secrets | Call `process.env.MAS_SERVICE_URL` from `app/api/.../route.ts`. Keeps API keys off the client. |
| **Same repo, server-only module** | Planner is TypeScript/Python invoked from Node | Expose it only inside Route Handlers or Server Actions; never import secrets into `app/page.tsx`. |
| **Direct browser → engine** | Public API with CORS + user auth | Simpler dev setup; harder to hide keys and to enforce rate limits. |

Long-running jobs (minutes) usually need **async jobs**: `POST` returns `jobId`, client polls `GET /api/plan/:jobId` or subscribes via SSE/WebSocket, then sets results when `status === "ready"`.

### 2. Map the form to your planner input

On submit, `InputScreen` passes a **`TripFormData`** object to `app/page.tsx` (see `handleFormSubmit`). Fields you will typically forward to your MAS:

| Field | Type | Role |
|-------|------|------|
| `origin`, `destination` | `string` | City names (same vocabulary as your geo/routing agents). |
| `query` | `string` | Free-text trip intent. |
| `dateRange` | `{ from?: Date; to?: Date }` (react-day-picker) | Serialize to ISO strings for your API. |
| `travelers` | `number` | Party size. |
| `budget` | `string` | User-entered budget (parse to number in your service if needed). |
| `roomType` | `string` | E.g. `Private Room`, `Entire Home`. |
| `houseRules` | `string[]` | Rule ids from the form (`pets`, `no-smoking`, …). |
| `cuisines` | `string[]` | Preferred cuisines. |
| `masStrategy` | `'budget' \| 'experience'` | High-level objective for agent weighting. |

Implement a **`POST /api/plan`** (name is arbitrary) that accepts this body (or your own DTO), calls the engine, and returns or streams the plan.

### 3. Target JSON shape (response contract)

The results view expects a **single trip object** compatible with `data/mock-travel-data.json`. Fields **read in `app/page.tsx`** today:

| Field | Type | Usage |
|-------|------|--------|
| `org` | `string` | Origin city label + globe marker (with `dest`). |
| `dest` | `string` | Destination city label + globe marker. |
| `days` | `number` | Shown in stats (“Duration”). |
| `people_number` | `number` | Fallback if form travelers not used in footer/stats. |
| `budget` | `number` | Fallback total budget when form budget is empty. |
| `itinerary` | array | Day-by-day cards (`ItineraryCards`). |

Each **itinerary day** should match what `components/itinerary-cards.tsx` expects (use `"-"` for empty slots; those rows are hidden):

```ts
// Conceptual shape — see mock file for real examples
type ItineraryDay = {
  day: number
  current_city: string
  transportation: string
  breakfast: string
  attraction: string
  lunch: string
  dinner: string
  accommodation: string
}
```

Extra mock fields (`date`, `visiting_city_number`, …) are optional unless you extend the UI to use them.

**Budget breakdown** (transportation / accommodation / food / activities percentages in the results grid) is **hardcoded** in `app/page.tsx`. For a real engine, replace those literals with fields from your response (e.g. `budget_breakdown: { transportation: { amount, pct }, ... }`) and wire them in the JSX.

### 4. Wire the client flow (what to change in code)

These steps are the minimal integration path:

1. **Stop using random data for real runs**  
   Remove or guard the `useEffect` in `app/page.tsx` that `fetch`es `GET /api/travel-data` on mount, or keep it only behind a `NEXT_PUBLIC_USE_MOCK_DATA=true` flag for demos.

2. **Trigger planning on submit**  
   When `handleFormSubmit` runs, either:
   - start a `fetch('/api/plan', { method: 'POST', body: JSON.stringify(data) })` and hold the result in state, or  
   - start a job and poll until complete.

3. **Align `LoadingScreen` with real latency**  
   Today it calls `onComplete` after a fixed duration (`totalDuration` in `components/loading-screen.tsx`). Replace that with: resolve when the plan request finishes (or when the job status is ready). Optionally drive `agentLogs` / phases from **SSE** or **WebSocket** events your MAS emits.

4. **Error handling**  
   If the engine fails, stay on or return to a dedicated error state; show `response.status` / `message` from your API. Consider timeout UX for slow agents.

5. **Globe coordinates**  
   `components/travel-globe.tsx` resolves cities via `data/uscities.json`. If your planner uses international or custom names, **extend that dataset** or add a geocoding step server-side and pass `lat`/`lng` through an expanded API contract (would require a small UI change to consume coordinates directly).

### 5. Security and operations

- Store **API keys and model endpoints** in environment variables; read them only in **server** code (Route Handlers, Server Actions, Edge only if compatible with your SDK).
- Enforce **auth** (session, JWT, API key per tenant) on your `POST /api/plan` before proxying to the engine.
- Add **rate limiting** and payload size limits on the BFF.
- Log **request ids** end-to-end (browser → Next → MAS) for debugging multi-agent traces.

### 6. Evolution path

- **Streaming tokens / reasoning**: optional second channel (SSE) while keeping the final itinerary JSON as the single source of truth for the bento grid.
- **Strong typing**: add a shared `TripPlan` Zod schema or OpenAPI spec and validate in the API route before the client receives data.
- **Testing**: keep `data/mock-travel-data.json` as a **fixture** for Storybook/tests and local UI work without calling the engine.

## Project layout (high level)

| Path | Role |
|------|------|
| `app/page.tsx` | Main flow: input → loading → results |
| `app/api/travel-data/route.ts` | Demo-only: random mock trip (`GET`). Replace with e.g. `POST /api/plan` when integrating your engine. |
| `components/input-screen.tsx` | Trip preference form |
| `components/loading-screen.tsx` | Transition after submit |
| `components/travel-globe.tsx` | Globe + city lookup |
| `components/itinerary-cards.tsx` | Expandable itinerary |
| `data/mock-travel-data.json` | Sample trips / itinerary schema |
| `data/uscities.json` | US city lat/lng for the globe |

## Configuration notes

- `next.config.mjs` sets `typescript.ignoreBuildErrors: true` and `images.unoptimized: true`. Tighten these when you are ready for stricter CI and optimized images.
- The 3D globe is loaded with `dynamic(..., { ssr: false })` so WebGL only runs in the browser.

## License

No license file is included in this repository; add one if you intend to distribute or open-source the project.

import { NextResponse } from 'next/server'
import travelData from '@/data/mock-travel-data.json'

export async function GET() {
  // Randomly select one itinerary object from the json list
  const randomIndex = Math.floor(Math.random() * travelData.length)
  const selectedTrip = travelData[randomIndex]
  
  // You can optionally add cache-control headers here to ensure random generation works across edge caching if deployed.
  const response = NextResponse.json(selectedTrip)
  response.headers.set('Cache-Control', 'no-store, max-age=0')
  return response
}

'use client';

import { Globe3D, GlobeMarker } from '@/components/ui/3d-globe';
import uscities from '@/data/uscities.json';

interface TravelGlobeProps {
  origin?: string;
  destination?: string;
}

export default function TravelGlobe({ origin = 'Provo', destination = 'Phoenix' }: TravelGlobeProps) {
  const travelMarkers: GlobeMarker[] = [];
  
  const getCityCoordinates = (cityName?: string) => {
    if (!cityName || typeof cityName !== "string") return null;

    const normalized = cityName.trim().toLowerCase();

    const cityData = (uscities as any[]).find((c) => {
      const city = c?.city?.toLowerCase?.();
      const ascii = c?.city_ascii?.toLowerCase?.();

      return city === normalized || ascii === normalized;
    });

    if (cityData) {
      return {
        lat: parseFloat(cityData.lat),
        lng: parseFloat(cityData.lng),
      };
    }

    return null;
  };

  const originCoords = getCityCoordinates(origin);
  if (originCoords) {
    travelMarkers.push({
      ...originCoords,
      src: `https://api.dicebear.com/7.x/avataaars/svg?seed=${origin.toLowerCase()}`,
      label: origin
    });
  }

  const destinationCoords = getCityCoordinates(destination);
  if (destinationCoords) {
    travelMarkers.push({
      ...destinationCoords,
      src: `https://api.dicebear.com/7.x/avataaars/svg?seed=${destination.toLowerCase()}`,
      label: destination
    });
  }
  const handleMarkerClick = (marker: GlobeMarker) => {
    console.log('Clicked:', marker.label);
  };

  const handleMarkerHover = (marker: GlobeMarker | null) => {
    if (marker) {
      console.log('Hovering:', marker.label);
    }
  };

  return (
    <div className="w-full h-full rounded-lg overflow-hidden">
      <Globe3D
        markers={travelMarkers}
        config={{
          atmosphereColor: '#4da6ff',
          atmosphereIntensity: 0,
          bumpScale: 1.5,
          autoRotateSpeed: 0.3,
          showAtmosphere: false,
          enableZoom: true,
          enablePan: true,
          minDistance: 3,
          maxDistance: 20,
          ambientIntensity: 2.5,
          pointLightIntensity: 0.8,
        }}
        onMarkerClick={handleMarkerClick}
        onMarkerHover={handleMarkerHover}
        className="h-full w-full"
      />
    </div>
  );
}

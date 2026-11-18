import { MapContainer, Marker, TileLayer, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { DEFAULT_ZOOM, OSM_ATTRIBUTION, OSM_TILE_URL, UCC_CENTER, markerIcon } from './config'

export interface MapPosition {
  latitude: number
  longitude: number
}

function ClickCapture({ onPick }: { onPick: (pos: MapPosition) => void }) {
  useMapEvents({
    click(e) {
      onPick({ latitude: e.latlng.lat, longitude: e.latlng.lng })
    },
  })
  return null
}

interface MapPickerProps {
  value: MapPosition | null
  onChange: (pos: MapPosition) => void
}

export function MapPicker({ value, onChange }: MapPickerProps) {
  return (
    <MapContainer
      center={value ? [value.latitude, value.longitude] : UCC_CENTER}
      zoom={DEFAULT_ZOOM}
      className="h-64 w-full rounded-xl border border-midnight/15"
      scrollWheelZoom
    >
      <TileLayer attribution={OSM_ATTRIBUTION} url={OSM_TILE_URL} />
      <ClickCapture onPick={onChange} />
      {value && (
        <Marker position={[value.latitude, value.longitude]} icon={markerIcon('FOUND')} />
      )}
    </MapContainer>
  )
}

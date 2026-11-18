import L from 'leaflet'

// University of Cape Coast (Cape Coast, Ghana) approximate centre.
export const UCC_CENTER: [number, number] = [5.1155, -1.2909]
export const DEFAULT_ZOOM = 15

export type MarkerKind = 'LOST' | 'FOUND' | 'RECOVERED'

const MARKER_COLORS: Record<MarkerKind, string> = {
  LOST: '#d97706', // amber
  FOUND: '#087f5b', // emerald green
  RECOVERED: '#64748b', // slate
}

const PIN_PATH =
  'M215.7 499.2C267 435 384 279.4 384 192C384 86 298 0 192 0S0 86 0 192c0 87.4 117 243 168.3 307.2c12.3 15.3 35.1 15.3 47.4 0zM192 128a64 64 0 1 1 0 128 64 64 0 1 1 0-128z'

export function markerIcon(kind: MarkerKind): L.DivIcon {
  const color = MARKER_COLORS[kind]
  const html = `<svg xmlns="http://www.w3.org/2000/svg" width="26" height="34" viewBox="0 0 384 512" fill="${color}" stroke="white" stroke-width="24" stroke-linejoin="round"><path d="${PIN_PATH}"/></svg>`
  return L.divIcon({
    className: '',
    html,
    iconSize: [26, 34],
    iconAnchor: [13, 34],
    popupAnchor: [0, -34],
  })
}

export const OSM_TILE_URL = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
export const OSM_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'

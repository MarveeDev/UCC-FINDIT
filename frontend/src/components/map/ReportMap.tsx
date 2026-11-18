import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet'
import { Link } from 'react-router-dom'
import 'leaflet/dist/leaflet.css'
import { DEFAULT_ZOOM, OSM_ATTRIBUTION, OSM_TILE_URL, markerIcon, type MarkerKind } from './config'
import type { ReportSummary } from '../../types'

function kindFor(report: ReportSummary): MarkerKind {
  if (report.status === 'RECOVERED') return 'RECOVERED'
  return report.report_type
}

function labelFor(kind: MarkerKind): string {
  if (kind === 'LOST') return 'Lost'
  if (kind === 'FOUND') return 'Found'
  return 'Recovered'
}

export function ReportMap({ reports }: { reports: ReportSummary[] }) {
  const points = reports
    .map((report) => {
      const lat = report.latitude ?? report.location_latitude
      const lng = report.longitude ?? report.location_longitude
      if (lat == null || lng == null) return null
      return { report, lat, lng }
    })
    .filter((p): p is { report: ReportSummary; lat: number; lng: number } => p !== null)

  if (points.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-dashed border-midnight/15 bg-white text-sm text-midnight/50">
        No reports with map coordinates to display.
      </div>
    )
  }

  const center: [number, number] = [points[0].lat, points[0].lng]

  return (
    <MapContainer
      center={center}
      zoom={DEFAULT_ZOOM}
      className="h-[420px] w-full rounded-xl border border-midnight/15"
      scrollWheelZoom
    >
      <TileLayer attribution={OSM_ATTRIBUTION} url={OSM_TILE_URL} />
      {points.map(({ report, lat, lng }) => {
        const kind = kindFor(report)
        return (
          <Marker key={report.id} position={[lat, lng]} icon={markerIcon(kind)}>
            <Popup>
              <div className="w-48">
                <span className="text-xs font-semibold text-brand">{labelFor(kind)}</span>
                <p className="mt-1 font-semibold text-midnight">{report.item_name}</p>
                <p className="text-xs text-midnight/60">
                  {report.location_name ?? 'Unknown location'}
                </p>
                <Link
                  to={`/items/${report.id}`}
                  className="mt-1 inline-block text-xs font-medium text-brand hover:underline"
                >
                  View details
                </Link>
              </div>
            </Popup>
          </Marker>
        )
      })}
    </MapContainer>
  )
}

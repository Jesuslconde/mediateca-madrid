export type Point = {
  latitud: number;
  longitud: number;
};

const EARTH_RADIUS_KM = 6371;

function toRadians(value: number): number {
  return (value * Math.PI) / 180;
}

export function haversineKm(a: Point, b: Point): number {
  const dLat = toRadians(b.latitud - a.latitud);
  const dLon = toRadians(b.longitud - a.longitud);
  const lat1 = toRadians(a.latitud);
  const lat2 = toRadians(b.latitud);

  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.min(1, Math.sqrt(h)));
}

export function formatDistance(km: number): string {
  if (km < 1) {
    const meters = Math.max(10, Math.round((km * 1000) / 10) * 10);
    return `≈ ${meters} m`;
  }
  const formatted = new Intl.NumberFormat("es-ES", {
    maximumFractionDigits: 1,
  }).format(km);
  return `≈ ${formatted} km`;
}

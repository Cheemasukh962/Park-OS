// The browser's Geolocation API, wrapped in a Promise. Free, no key: the browser asks the user's
// permission and only works on https or localhost, and only while the page is open.

export type LatLng = { lat: number; lng: number };

export const CAMPUS_CENTRE: LatLng = { lat: 38.5382, lng: -121.7617 };

export function currentLocation(): Promise<LatLng> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error("This browser can't share its location. Pick a class building instead."));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => resolve({ lat: position.coords.latitude, lng: position.coords.longitude }),
      (error) => reject(new Error(
        error.code === error.PERMISSION_DENIED ? "Location permission was denied. Allow it in the browser, or pick a class building instead."
        : error.code === error.TIMEOUT ? "Finding your location took too long. Try again, or pick a class building."
        : "Couldn't find your location. Try again, or pick a class building.")),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  });
}

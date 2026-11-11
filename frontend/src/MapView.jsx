import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Pins are numbered by queue rank and coloured by tier. They are plain HTML (divIcon), so they
// render even when the OpenStreetMap tiles cannot load (no internet).
export default function MapView({ queue, selected, onSelect }) {
  const el = useRef(null);
  const map = useRef(null);
  const layer = useRef(null);
  const fitted = useRef(false);

  useEffect(() => {
    map.current = L.map(el.current, { zoomControl: true }).setView([21.94, 88.85], 11);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: "© OpenStreetMap contributors",
    }).addTo(map.current);
    layer.current = L.layerGroup().addTo(map.current);
    return () => {
      map.current.remove();
      map.current = null;
      fitted.current = false;
    };
  }, []);

  useEffect(() => {
    if (!map.current) return;
    layer.current.clearLayers();
    const points = [];
    // draw lower-ranked first so top-priority pins sit on top
    [...queue].reverse().forEach((inc) => {
      if (inc.lat == null || inc.lon == null) return;
      const rank = queue.indexOf(inc) + 1;
      const icon = L.divIcon({
        className: "",
        html: `<div class="pin pin-${inc.effective_tier} ${selected === inc.id ? "sel" : ""}">${rank}</div>`,
        iconSize: [34, 34],
        iconAnchor: [17, 17],
      });
      // Leaflet stacks markers by screen position first, so the offset must be large enough to
      // override that: higher rank (smaller number) on top, selected pin above everything.
      const z = (selected === inc.id ? 100000 : 0) + (50 - rank) * 1000;
      L.marker([inc.lat, inc.lon], { icon, zIndexOffset: z })
        .on("click", () => onSelect(inc.id))
        .bindTooltip(`${inc.effective_tier} · ${inc.summary.slice(0, 60)}`)
        .addTo(layer.current);
      points.push([inc.lat, inc.lon]);
    });
    if (points.length && !fitted.current) {
      map.current.fitBounds(points, { padding: [40, 40], maxZoom: 13 });
      fitted.current = true;
    }
    if (!points.length) fitted.current = false;
  }, [queue, selected, onSelect]);

  return <div ref={el} className="map" />;
}

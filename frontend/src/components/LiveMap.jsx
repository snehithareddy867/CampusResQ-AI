import React, { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from "react-leaflet";
import L from "leaflet";

// Fix default marker icons for CRA/webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const emergencyIcon = L.divIcon({
  html: `<div style="background:#EF4444;width:22px;height:22px;border-radius:50%;border:3px solid #fff;box-shadow:0 0 12px rgba(239,68,68,.6)"></div>`,
  className: "", iconSize: [22, 22], iconAnchor: [11, 11],
});
function responderIconHtml(heading) {
  const arrow = heading != null ? `<div style="position:absolute;top:-14px;left:50%;transform:translateX(-50%) rotate(${heading}deg);transform-origin:center 24px;width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-bottom:10px solid #00E5FF;"></div>` : "";
  return `<div style="position:relative"><div style="background:#00E5FF;width:20px;height:20px;border-radius:50%;border:3px solid #0A192F;box-shadow:0 0 12px rgba(0,229,255,.7)"></div>${arrow}</div>`;
}

function Recenter({ center }) {
  const map = useMap();
  useEffect(() => { if (center) map.setView(center, map.getZoom()); }, [center, map]);
  return null;
}

export default function LiveMap({ incident, height = 320, markers = [] }) {
  const center = incident?.location
    ? [incident.location.lat, incident.location.lng]
    : (markers[0] ? [markers[0].lat, markers[0].lng] : [12.9716, 77.5946]);

  return (
    <div data-testid="live-map" className="rounded-xl overflow-hidden border border-slate-200" style={{ height }}>
      <MapContainer center={center} zoom={16} style={{ height: "100%", width: "100%" }} scrollWheelZoom={false}>
        <TileLayer attribution='&copy; OpenStreetMap' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <Recenter center={center} />
        {incident?.location && (
          <Marker position={[incident.location.lat, incident.location.lng]} icon={emergencyIcon}>
            <Popup>Emergency location</Popup>
          </Marker>
        )}
        {incident?.responder_location && (
          <>
            <Marker
              position={[incident.responder_location.lat, incident.responder_location.lng]}
              icon={L.divIcon({ html: responderIconHtml(incident.responder_location.heading), className: "", iconSize: [20, 20], iconAnchor: [10, 10] })}>
              <Popup>{incident.assigned_responder_name || "Responder"}<br/>{incident.responder_location.speed_mps != null ? `${(incident.responder_location.speed_mps*3.6).toFixed(1)} km/h` : ""}</Popup>
            </Marker>
            <Polyline
              positions={[
                [incident.responder_location.lat, incident.responder_location.lng],
                [incident.location.lat, incident.location.lng],
              ]}
              pathOptions={{ color: "#00E5FF", weight: 3, dashArray: "6 6" }}
            />
          </>
        )}
        {markers.map((m, i) => (
          <Marker key={i} position={[m.lat, m.lng]} icon={m.critical ? emergencyIcon : L.divIcon({ html: responderIconHtml(), className: "", iconSize: [20, 20], iconAnchor: [10, 10] })}>
            <Popup>{m.label}</Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}

"use client";

import { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";

const Heatmap = ({ data }) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const heatLayerRef = useRef(null);

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;
    if (!data || data.length === 0) return;

    const initMap = async () => {
      // Import Leaflet and heat plugin
      const L = (await import("leaflet")).default;
      await import("leaflet.heat");

      // Initialize map
      const map = L.map(mapRef.current, {
        center: [20, 0],
        zoom: 2,
        zoomControl: true,
        scrollWheelZoom: true,
      });

      // Add OpenStreetMap tiles
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution:
          '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      }).addTo(map);

      // Convert data to heatmap format [lat, lng, intensity]
      const heatData = data.map((node) => [node.lat, node.lng, 1]);

      // Create and add heat layer
      const heat = L.heatLayer(heatData, {
        radius: 25,
        blur: 15,
        maxZoom: 17,
        max: 1.0,
        gradient: {
          0.0: "blue",
          0.5: "lime",
          0.7: "yellow",
          1.0: "red",
        },
      }).addTo(map);

      mapInstanceRef.current = map;
      heatLayerRef.current = heat;

      console.log(
        `🗺️ Heatmap rendered with ${data.length.toLocaleString()} peer locations`
      );
    };

    initMap();

    // Cleanup
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        heatLayerRef.current = null;
      }
    };
  }, [data]);

  if (!data || data.length === 0) {
    return (
      <div
        style={{
          padding: "20px",
          color: "#f59e0b",
          textAlign: "center",
          border: "2px solid #f59e0b",
          borderRadius: "10px",
          margin: "20px",
          background: "#fffbeb",
        }}
      >
        <h3>⚠️ No Data Available</h3>
        <p>No geolocated peers found in the database.</p>
        <p style={{ fontSize: "0.9em", color: "#92400e", marginTop: "10px" }}>
          Make sure the backend API is running and has geolocated peer data.
        </p>
      </div>
    );
  }

  return (
    <div
      ref={mapRef}
      style={{
        width: "100%",
        height: "600px",
        borderRadius: "12px",
        overflow: "hidden",
      }}
    />
  );
};

export default Heatmap;

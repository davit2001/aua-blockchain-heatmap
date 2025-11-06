"use client";

import { useEffect, useRef } from "react";

const Heatmap = ({ data }) => {
    const mapRef = useRef(null);

    useEffect(() => {
        function initMap() {
            const { google } = window;
            if (!google || !google.maps) {
                console.warn("Google Maps not fully loaded yet");
                return;
            }

            console.log("Google Maps loaded", google.maps);

            const sanFrancisco = new google.maps.LatLng(37.774546, -122.433523);

            const map = new google.maps.Map(mapRef.current, {
                center: sanFrancisco,
                zoom: 13,
                mapTypeId: "satellite",
            });

            const heatmapData = data.map(
                (node) => new google.maps.LatLng(node.latitude, node.longitude)
            );

            const heatmap = new google.maps.visualization.HeatmapLayer({
                data: heatmapData,
            });

            heatmap.setMap(map);
        }

        // --- Load Google Maps script safely ---
        const existingScript = document.getElementById("googleMapsScript");

        if (!existingScript) {
            console.log('process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY', process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY)
            const script = document.createElement("script");
            script.id = "googleMapsScript";
            script.src = `https://maps.googleapis.com/maps/api/js?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&libraries=visualization`;
            script.async = true;
            script.defer = true;

            // Use this to ensure full load before calling initMap
            script.addEventListener("load", () => {
                // Small delay ensures constructors (LatLng, Map, etc.) are initialized
                setTimeout(initMap, 200);
            });

            document.body.appendChild(script);
        } else {
            if (window.google && window.google.maps) {
                initMap();
            } else {
                existingScript.addEventListener("load", () => {
                    setTimeout(initMap, 200);
                });
            }
        }
    }, [data]);

    return (
        <div
            ref={mapRef}
            style={{
                width: "100%",
                height: "500px",
                borderRadius: "10px",
                overflow: "hidden",
            }}
        />
    );
};

export default Heatmap;
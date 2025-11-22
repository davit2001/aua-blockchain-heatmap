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

            const sanFrancisco = new google.maps.LatLng(40.1935695, 44.5034762);

            const map = new google.maps.Map(mapRef.current, {
                center: sanFrancisco,
                zoom: 20,
                mapTypeId: "roadmap",
            });

            const heatmapData = data.map(
                (node) => new google.maps.LatLng(node.latitude, node.longitude)
            );

            const heatmap = new google.maps.visualization.HeatmapLayer({
                data: heatmapData,
            });

            heatmap.setMap(map);
        }

        const existingScript = document.getElementById("googleMapsScript");

        if (!existingScript) {
            const script = document.createElement("script");
            script.id = "googleMapsScript";
            script.src = `https://maps.googleapis.com/maps/api/js?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&libraries=visualization`;
            script.async = true;
            script.defer = true;

            script.addEventListener("load", () => {
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
                maxWidth: "1200px",
                borderRadius: '16px',
                height: "500px",
            }}
        />
    );
};

export default Heatmap;
export function mountGeoHeatmap(container, data) {
    const geoData = data.geo_data || [];

    container.innerHTML = `
        <div class="page-title">
            <h1>Geographic Distribution</h1>
            <p>Intelligence nodes across global capitals and conflict zones.</p>
        </div>

        <div class="grid grid--2 mt-8" style="grid-template-columns: 2fr 1fr; gap: 2rem;">
            <div class="torn-wrapper" style="filter: drop-shadow(0 10px 20px rgba(0,0,0,0.2));">
                <div class="torn-container" style="padding: 0; min-height: 500px; max-width: 900px;">
                    <div id="map" style="height: 500px; background: var(--parchment-light); filter: sepia(0.1) contrast(1.05);"></div>
                </div>
            </div>

            <div class="list-ink" style="display: flex; flex-direction: column; gap: 1.5rem;">
                <div class="torn-wrapper">
                    <div class="torn-container" style="padding: 1.5rem;">
                        <span class="card-category">Intelligence Hotspots</span>
                        <h3 class="card-title">Top Mentioned Regions</h3>
                        <div class="list-ink">
                            ${geoData.slice(0, 8).map(loc => `
                                <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px dashed var(--outline);">
                                    <span style="font-family: var(--font-heading); font-weight: 700;">${loc.location_name}</span>
                                    <span class="bold" style="font-family: var(--font-sketch);">${loc.total_mentions}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>

                <div class="torn-wrapper">
                    <div class="torn-container" style="padding: 1.5rem;">
                        <span class="card-category">Signal Key</span>
                        <div style="height: 8px; background: linear-gradient(to right, #f4e9d9, #5a3c1e); border: 1px solid var(--outline); margin: 1rem 0 0.5rem;"></div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.7rem; font-family: var(--font-sketch);">
                            <span>LOW SIGNAL</span>
                            <span>CRITICAL</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="grid grid--3 mt-8">
            <div class="torn-wrapper">
                <div class="torn-container">
                    <span class="card-category">Field Intelligence</span>
                    <h3 class="card-title">Impact Intensity</h3>
                    <p class="italic text-sm">Frequency of geographic mentions in headlines dictates nodal scale.</p>
                </div>
            </div>
            <div class="torn-wrapper">
                <div class="torn-container">
                    <span class="card-category">Location Sentiment</span>
                    <h3 class="card-title">Regional Polarity</h3>
                    <div class="list-ink">
                        ${geoData.slice(0, 3).map(loc => `
                            <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-bottom: 1px dashed var(--outline);">
                                <span style="font-family: var(--font-heading); font-weight: 700;">${loc.location_name}</span>
                                <span class="${loc.avg_polarity > 0 ? 'text-pos' : 'text-neg'}" style="font-weight: 900;">
                                    ${loc.avg_polarity > 0 ? '+' : ''}${loc.avg_polarity?.toFixed(2)}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
            <div class="torn-wrapper">
                <div class="torn-container">
                    <span class="card-category">Map Interaction</span>
                    <h3 class="card-title">Nodal Recon</h3>
                    <p class="italic text-sm">Hover over intelligence nodes to retrieve specific regional metadata.</p>
                </div>
            </div>
        </div>
    `;

    // Initialize map with a slight delay to ensure container is ready
    setTimeout(() => {
        if (!document.getElementById('map')) return;

        const map = L.map('map', { 
            center: [20, 10], 
            zoom: 2,
            zoomControl: false,
            scrollWheelZoom: true
        });
        
        L.control.zoom({ position: 'bottomright' }).addTo(map);

        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        setTimeout(() => map.invalidateSize(), 200);

        // Subtle heatmap layer
        if (window.L && L.heatLayer && geoData.length > 0) {
            const heatPoints = geoData.map(loc => [
                loc.lat, 
                loc.lng, 
                Math.min(loc.total_mentions / 50, 0.8) // Capped intensity
            ]);
            
            L.heatLayer(heatPoints, { 
                radius: 15, // Much smaller radius
                blur: 20,
                maxZoom: 4,
                max: 1.0,
                gradient: { 0.4: '#d4c5b0', 0.6: '#a68a64', 1: '#5a3c1e' }
            }).addTo(map);
        }
        
        // Hover-triggered markers
        geoData.forEach(loc => {
            const color = loc.avg_polarity > 0 ? '#1b4d3e' : '#8b0000';
            const marker = L.circleMarker([loc.lat, loc.lng], {
                radius: Math.max(4, Math.sqrt(loc.total_mentions) * 1.2), // Slightly smaller dots
                fillColor: color,
                color: '#2d1b0d',
                weight: 1,
                fillOpacity: 0.7
            });

            const popupContent = `
                <div style="font-family: var(--font-heading); color: #2d1b0d; min-width: 120px;">
                    <h4 style="margin: 0; border-bottom: 1px solid var(--outline); font-size: 1rem;">${loc.location_name}</h4>
                    <div style="margin-top: 0.5rem; font-size: 0.8rem;">
                        <p style="margin: 0;">Mentions: <b>${loc.total_mentions}</b></p>
                        <p style="margin: 0;">Sentiment: <b class="${loc.avg_polarity > 0 ? 'text-pos' : 'text-neg'}">${loc.avg_polarity?.toFixed(2)}</b></p>
                    </div>
                </div>
            `;

            marker.bindPopup(popupContent, { closeButton: false, offset: [0, -5] });

            // Hover interactions
            marker.on('mouseover', function(e) {
                this.openPopup();
                this.setStyle({ fillOpacity: 1, weight: 2 });
            });
            marker.on('mouseout', function(e) {
                this.closePopup();
                this.setStyle({ fillOpacity: 0.7, weight: 1 });
            });

            marker.addTo(map);
        });

        window._leafletMap = map;
    }, 100);
}

export function unmountGeoHeatmap() {
    if (window._leafletMap) {
        window._leafletMap.remove();
        window._leafletMap = null;
    }
}

const GEO_COORDS = {
  'US': [38.9, -77.0], 'USA': [38.9, -77.0], 'United States': [38.9, -77.0],
  'Ukraine': [50.4, 30.5], 'Russia': [55.7, 37.6], 'China': [39.9, 116.4],
  'Israel': [31.8, 35.2], 'Gaza': [31.5, 34.5], 'Iran': [35.7, 51.4],
  'India': [28.6, 77.2], 'Pakistan': [33.7, 73.1], 'UK': [51.5, -0.1],
  'Britain': [51.5, -0.1], 'France': [48.9, 2.3], 'Germany': [52.5, 13.4],
  'Brazil': [-15.8, -47.9], 'Venezuela': [10.5, -66.9], 'Cuba': [23.1, -82.4],
  'Nigeria': [9.1, 7.5], 'Tanzania': [-6.8, 39.3], 'Congo': [-4.3, 15.3],
  'DR Congo': [-4.3, 15.3], 'Uganda': [0.3, 32.6], 'Lebanon': [33.9, 35.5],
  'Taiwan': [25.0, 121.5], 'Japan': [35.7, 139.7], 'Peru': [-12.0, -77.0],
  'Switzerland': [46.9, 7.4], 'London': [51.5, -0.1], 'Beijing': [39.9, 116.4]
};

const GPE_REGIONS = {
  'US': 'North America', 'USA': 'North America', 'United States': 'North America',
  'Ukraine': 'Europe', 'Russia': 'Europe', 'China': 'East Asia',
  'Israel': 'Middle East', 'Gaza': 'Middle East', 'Iran': 'Middle East',
  'India': 'South Asia', 'Pakistan': 'South Asia', 'UK': 'Europe',
  'Britain': 'Europe', 'France': 'Europe', 'Germany': 'Europe',
  'Brazil': 'Latin America', 'Venezuela': 'Latin America', 'Cuba': 'Latin America',
  'Nigeria': 'Sub-Saharan Africa', 'Tanzania': 'Sub-Saharan Africa', 'Congo': 'Sub-Saharan Africa',
  'DR Congo': 'Sub-Saharan Africa', 'Uganda': 'Sub-Saharan Africa', 'Lebanon': 'Middle East',
  'Taiwan': 'East Asia', 'Japan': 'East Asia', 'Peru': 'Latin America',
  'Switzerland': 'Europe', 'London': 'Europe', 'Beijing': 'East Asia'
};

function findRepresentativeHeadline(locationName, headlines) {
    if (!headlines || headlines.length === 0) return null;
    
    const lowerName = locationName.toLowerCase();
    const variants = [lowerName];
    if (lowerName === 'us' || lowerName === 'usa') {
        variants.push('u.s.', 'united states', 'america');
    } else if (lowerName === 'uk') {
        variants.push('u.k.', 'britain', 'united kingdom', 'london');
    } else if (lowerName === 'russia') {
        variants.push('russian', 'moscow');
    } else if (lowerName === 'china') {
        variants.push('chinese', 'beijing');
    } else if (lowerName === 'israel') {
        variants.push('israeli', 'tel aviv');
    } else if (lowerName === 'gaza') {
        variants.push('gazan', 'palestinian');
    } else if (lowerName === 'india') {
        variants.push('indian', 'delhi');
    }
    
    const matches = headlines.filter(h => {
        const text = (h.Translated_Headline || '').toLowerCase();
        return variants.some(v => text.includes(v));
    });
    
    if (matches.length === 0) return null;
    
    let best = matches[0];
    let maxAbs = Math.abs(best.Polarity || 0);
    for (let i = 1; i < matches.length; i++) {
        const abs = Math.abs(matches[i].Polarity || 0);
        if (abs > maxAbs) {
            maxAbs = abs;
            best = matches[i];
        }
    }
    return best.Translated_Headline;
}

export function mountGeoHeatmap(container, data) {
    const geoData = data.geo_data || [];

    // 1. Resolve coordinates and filter out invalid/missing locations
    const mapPoints = [];
    geoData.forEach(loc => {
        if (!loc.location_name) return;
        let lat = null;
        let lng = null;
        const name = loc.location_name.trim();
        
        if (GEO_COORDS[name]) {
            [lat, lng] = GEO_COORDS[name];
        } else if (loc.lat !== undefined && loc.lng !== undefined && loc.lat !== null && loc.lng !== null) {
            const lLat = Number(loc.lat);
            const lLng = Number(loc.lng);
            if (lLat !== 0 || lLng !== 0) {
                lat = lLat;
                lng = lLng;
            }
        }
        
        if (lat !== null && lng !== null) {
            mapPoints.push({
                ...loc,
                lat,
                lng
            });
        }
    });

    // 2. Pre-map entity sources from entities list
    const entitySourcesMap = {};
    if (data.entities && data.entities.entities) {
        data.entities.entities.forEach(ent => {
            if (ent.label === 'GPE') {
                entitySourcesMap[ent.name] = ent.sources || {};
            }
        });
    }

    // 3. Extract unique source names
    const allSourcesSet = new Set();
    if (data.entities && data.entities.entities) {
        data.entities.entities.forEach(ent => {
            if (ent.label === 'GPE' && ent.sources) {
                Object.keys(ent.sources).forEach(src => {
                    if (src !== 'Other') {
                        allSourcesSet.add(src);
                    }
                });
            }
        });
    }
    const availableSources = Array.from(allSourcesSet).sort();

    // 4. Panel 1 data logic (Coverage Intensity: top 8)
    const rankedPoints = [...mapPoints].sort((a, b) => b.total_mentions - a.total_mentions);
    const top8Points = rankedPoints.slice(0, 8);
    const maxMentions = top8Points.length > 0 ? Math.max(...top8Points.map(p => p.total_mentions)) : 1;

    // 5. Panel 2 data logic (Regional Tone: top 6)
    const top6Points = rankedPoints.slice(0, 6);
    const getPolarityColor = (val) => {
        if (val > 0.05) return 'color: var(--tertiary, #1b4d3e); font-weight: 900;';
        if (val < -0.05) return 'color: var(--primary, #8b0000); font-weight: 900;';
        return 'color: var(--outline, #1a1a1a); font-weight: 900;';
    };

    // 6. Panel 3 data logic (Coverage Gaps)
    const regionCounts = {
        'Sub-Saharan Africa': 0,
        'Latin America': 0,
        'Middle East': 0,
        'East Asia': 0,
        'South Asia': 0,
        'Europe': 0
    };
    mapPoints.forEach(loc => {
        const r = GPE_REGIONS[loc.location_name];
        if (r && regionCounts[r] !== undefined) {
            regionCounts[r]++;
        }
    });

    const gaps = [];
    if (regionCounts['Sub-Saharan Africa'] < 3) {
        gaps.push({ name: 'Sub-Saharan Africa', reason: 'Critical lack of correspondents and reporting nodes.' });
    }
    if (regionCounts['Latin America'] < 3) {
        gaps.push({ name: 'Latin America', reason: 'Zero mentions across main wire feeds in this period.' });
    }
    if (regionCounts['Middle East'] < 3) {
        gaps.push({ name: 'Middle East', reason: 'No significant news signals captured.' });
    }
    if (regionCounts['East Asia'] < 3) {
        gaps.push({ name: 'East Asia', reason: 'Under-reported regional developments.' });
    }
    if (regionCounts['South Asia'] < 3) {
        gaps.push({ name: 'South Asia', reason: 'Minimal signal intensity detected.' });
    }
    if (regionCounts['Europe'] < 3) {
        gaps.push({ name: 'Europe', reason: 'Quiet regional wire reporting.' });
    }
    if (gaps.length === 0) {
        gaps.push({ name: 'Sub-Saharan Africa', reason: 'Minimal correspondent presence.' });
    }

    container.innerHTML = `
        <div class="page-title">
            <h1>Geographic Distribution</h1>
            <p>Intelligence nodes across global capitals and conflict zones.</p>
        </div>

        <!-- Full-width Map Container with Absolute-positioned Dropdown Control -->
        <div class="torn-wrapper mt-8" style="filter: drop-shadow(0 10px 20px rgba(0,0,0,0.2)); width: 100%;">
            <div class="torn-container" style="padding: 0; min-height: 500px; width: 100%; position: relative;">
                <div id="map" style="height: 500px; background: #121212; width: 100%;"></div>
                
                <!-- Floating Source Filter Control -->
                <div id="sourceFilterControl" style="position: absolute; top: 16px; right: 16px; z-index: 1000; font-family: 'Inter', sans-serif;">
                    <button id="filterDropdownBtn" style="padding: 8px 16px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; border: 1px solid var(--outline); background: #f4ecd8; color: #1a1a1a; cursor: pointer; display: flex; align-items: center; gap: 8px; box-shadow: 2px 2px 0px rgba(0,0,0,0.15); transition: all 0.2s ease;">
                        <span>SOURCE: ALL</span>
                        <span style="font-size: 8px;">▼</span>
                    </button>
                    <div id="filterDropdownMenu" style="display: none; position: absolute; top: 100%; right: 0; margin-top: 4px; background: #f4ecd8; border: 1px solid var(--outline); box-shadow: 4px 4px 0px rgba(0,0,0,0.3); width: 180px; max-height: 250px; overflow-y: auto; flex-direction: column; z-index: 1001;">
                        <button data-source="ALL" class="dropdown-item active-item" style="padding: 8px 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; text-align: left; background: var(--primary); color: #fdfaf5; border: none; cursor: pointer; width: 100%; transition: all 0.1s ease;">
                            ALL SOURCES
                        </button>
                        ${availableSources.map(src => `
                            <button data-source="${src}" class="dropdown-item" style="padding: 8px 12px; font-size: 10px; font-weight: 700; text-transform: uppercase; text-align: left; background: none; color: #1a1a1a; border: none; cursor: pointer; width: 100%; transition: all 0.1s ease; border-top: 1px dashed rgba(26,26,26,0.1);">
                                ${src}
                            </button>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>

        <!-- 3-Column Grid for Panels -->
        <div class="grid grid--3 mt-8" style="gap: 1.5rem;">
            <!-- Panel 1: Coverage Intensity -->
            <div class="torn-wrapper">
                <div class="torn-container" style="padding: 1.5rem; min-height: 400px; display: flex; flex-direction: column;">
                    <span class="card-category" style="font-variant: all-small-caps; letter-spacing: 0.05em; font-size: 0.95rem;">COVERAGE INTENSITY</span>
                    <div style="font-family: 'IBM Plex Serif', serif; font-style: italic; font-size: 13px; color: var(--text-muted); margin-bottom: 16px; line-height: 1.4;">
                        Bubble size reflects mention frequency across all sources — larger bubbles indicate higher news gravity.
                    </div>
                    <div class="list-ink" style="display: flex; flex-direction: column; gap: 12px; flex: 1; justify-content: space-between;">
                        ${top8Points.map(loc => {
                            const percentage = (loc.total_mentions / maxMentions) * 100;
                            return `
                                <div class="actor-item" style="display: flex; flex-direction: column; gap: 4px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="font-family: var(--font-heading); font-weight: 700; color: var(--text); font-size: 0.9rem;">${loc.location_name}</span>
                                        <span style="font-family: var(--font-mono); font-size: 0.75rem; color: var(--primary); font-weight: 700;">[${loc.total_mentions}]</span>
                                    </div>
                                    <div style="height: 6px; background: rgba(90, 60, 30, 0.08); border: 1px solid var(--outline); width: 100%;">
                                        <div style="width: ${percentage}%; background: var(--primary); height: 100%;"></div>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
            </div>

            <!-- Panel 2: Sentiment by Region -->
            <div class="torn-wrapper">
                <div class="torn-container" style="padding: 1.5rem; min-height: 400px; display: flex; flex-direction: column;">
                    <span class="card-category" style="font-variant: all-small-caps; letter-spacing: 0.05em; font-size: 0.95rem;">REGIONAL TONE</span>
                    <div style="font-family: 'IBM Plex Serif', serif; font-style: italic; font-size: 13px; color: var(--text-muted); margin-bottom: 16px; line-height: 1.4;">
                        Polarity score reflects average emotional tone of headlines mentioning this location. Negative scores indicate crisis or conflict coverage.
                    </div>
                    <div class="list-ink" style="display: flex; flex-direction: column; gap: 8px; flex: 1; justify-content: space-between;">
                        ${top6Points.map(loc => `
                            <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px dashed var(--outline); align-items: center;">
                                <span style="font-family: var(--font-heading); font-weight: 700; font-size: 0.9rem;">${loc.location_name}</span>
                                <span style="${getPolarityColor(loc.avg_polarity)} font-size: 0.95rem;">
                                    ${loc.avg_polarity > 0.05 ? '+' : ''}${loc.avg_polarity?.toFixed(2)}
                                </span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>

            <!-- Panel 3: Coverage Gap Analysis -->
            <div class="torn-wrapper">
                <div class="torn-container" style="padding: 1.5rem; min-height: 400px; display: flex; flex-direction: column;">
                    <span class="card-category" style="font-variant: all-small-caps; letter-spacing: 0.05em; font-size: 0.95rem;">COVERAGE GAPS</span>
                    <div style="font-family: 'IBM Plex Serif', serif; font-style: italic; font-size: 13px; color: var(--text-muted); margin-bottom: 16px; line-height: 1.4;">
                        Regions absent from coverage reveal the geographic blind spots of the monitored source network.
                    </div>
                    <div class="list-ink" style="display: flex; flex-direction: column; gap: 14px; flex: 1; justify-content: flex-start; margin-top: 10px;">
                        ${gaps.slice(0, 4).map(gap => `
                            <div style="padding-bottom: 0.5rem; border-bottom: 1px dashed var(--outline);">
                                <div style="font-family: var(--font-heading); font-weight: 700; color: var(--primary); font-size: 0.95rem; text-transform: uppercase;">${gap.name}</div>
                                <div style="font-size: 0.8rem; color: var(--text-muted); font-style: italic; margin-top: 2px;">${gap.reason}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;

    // Initialize map
    setTimeout(() => {
        if (!document.getElementById('map')) return;

        const map = L.map('map', { 
            zoomControl: false,
            scrollWheelZoom: true,
            maxBounds: [[-85, -180], [85, 180]],
            maxBoundsViscosity: 1.0,
            minZoom: 2,
            maxZoom: 8,
            zoomSnap: 0.5
        });
        map.setView([20, 15], 2);
        
        L.control.zoom({ position: 'bottomright' }).addTo(map);

        // Base dark gray canvas
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
            maxZoom: 8,
            minZoom: 2
        }).addTo(map);

        // Reference labels in English
        L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}', {
            attribution: 'Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ',
            maxZoom: 8,
            minZoom: 2
        }).addTo(map);

        setTimeout(() => map.invalidateSize(), 200);

        // Initial plot of all points
        replotMapBubbles(map, mapPoints, entitySourcesMap, null, data.recent_headlines);

        // Wire dropdown filter
        wireDropdownFilter(container, map, mapPoints, entitySourcesMap, data.recent_headlines);

        window._leafletMap = map;
    }, 100);
}

function replotMapBubbles(map, mapPoints, entitySourcesMap, selectedSource, recentHeadlines) {
    if (map._customMarkers) {
        map._customMarkers.forEach(m => map.removeLayer(m));
    }
    map._customMarkers = [];
    
    if (map._heatmapLayer) {
        map.removeLayer(map._heatmapLayer);
        map._heatmapLayer = null;
    }
    
    const filteredPoints = [];
    mapPoints.forEach(loc => {
        let mentions = loc.total_mentions;
        if (selectedSource) {
            mentions = entitySourcesMap[loc.location_name]?.[selectedSource] || 0;
        }
        
        if (mentions > 0) {
            filteredPoints.push({
                ...loc,
                display_mentions: mentions
            });
        }
    });
    
    // Add heatmap layer
    if (window.L && L.heatLayer && filteredPoints.length > 0) {
        const heatPoints = filteredPoints.map(loc => [
            loc.lat, 
            loc.lng, 
            Math.min(loc.display_mentions / 50, 0.8)
        ]);
        
        map._heatmapLayer = L.heatLayer(heatPoints, { 
            radius: 15,
            blur: 20,
            maxZoom: 4,
            max: 1.0,
            gradient: { 0.4: '#1a1a1a', 0.6: '#5a3c1e', 1: '#d4c5b0' }
        }).addTo(map);
    }
    
    // Add markers
    filteredPoints.forEach(loc => {
        const color = loc.avg_polarity > 0 ? '#4caf50' : '#f44336';
        
        // Scale radius slightly depending on total vs filtered count
        const scaleFactor = selectedSource ? 2.5 : 1.2;
        const radius = Math.max(4, Math.sqrt(loc.display_mentions) * scaleFactor);

        const marker = L.circleMarker([loc.lat, loc.lng], {
            radius: radius,
            fillColor: color,
            color: '#121212',
            weight: 1.5,
            fillOpacity: 0.8
        });

        // Get top 2 sources
        const sources = entitySourcesMap[loc.location_name] || {};
        const sortedSources = Object.entries(sources)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 2)
            .map(entry => `${entry[0]} (${entry[1]})`);
        const sourcesText = sortedSources.length > 0 ? sortedSources.join(', ') : 'None';

        // Get representative headline
        const repHeadline = findRepresentativeHeadline(loc.location_name, recentHeadlines);

        // Format polarity
        const pol = loc.avg_polarity || 0;
        const polColor = pol > 0.05 ? '#81c784' : (pol < -0.05 ? '#e57373' : '#c9a96e');
        const polSign = pol > 0.05 ? '+' : '';

        const popupContent = `
            <div style="min-width: 180px; text-align: left;">
                <h4 style="font-family: 'Old Standard TT', serif; font-size: 1.1rem; font-weight: 700; color: #fdfaf5; margin: 0 0 6px; border-bottom: 1px solid #5a3c1e; padding-bottom: 4px;">${loc.location_name}</h4>
                <div style="font-size: 0.8rem; margin-bottom: 4px; color: #c9a96e;">Mentions: <b style="color: #fdfaf5;">${loc.display_mentions} mentions</b></div>
                <div style="font-size: 0.8rem; margin-bottom: 8px; color: #c9a96e;">Avg Polarity: <b style="color: ${polColor};">${polSign}${pol.toFixed(2)}</b></div>
                <div style="font-size: 0.75rem; margin-bottom: 8px; border-top: 1px dashed rgba(90, 60, 30, 0.3); padding-top: 6px; color: #a68a64;">Top Sources: <i>${sourcesText}</i></div>
                ${repHeadline ? `<div style="font-size: 0.75rem; border-top: 1px dashed rgba(90, 60, 30, 0.3); padding-top: 6px; font-style: italic; line-height: 1.35; color: #d4c5b0; word-wrap: break-word;">"${repHeadline}"</div>` : ''}
            </div>
        `;

        marker.bindPopup(popupContent, { 
            closeButton: false, 
            offset: [0, -5],
            className: 'custom-map-popup'
        });

        marker.on('mouseover', function(e) {
            this.openPopup();
            this.setStyle({ fillOpacity: 1, weight: 2 });
        });
        marker.on('mouseout', function(e) {
            this.closePopup();
            this.setStyle({ fillOpacity: 0.8, weight: 1.5 });
        });

        marker.addTo(map);
        map._customMarkers.push(marker);
    });
}

function wireDropdownFilter(container, map, mapPoints, entitySourcesMap, recentHeadlines) {
    const btn = container.querySelector('#filterDropdownBtn');
    const menu = container.querySelector('#filterDropdownMenu');
    if (!btn || !menu) return;
    
    // Toggle menu
    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = menu.style.display === 'flex';
        menu.style.display = isOpen ? 'none' : 'flex';
    });

    // Close menu when clicking outside
    document.addEventListener('click', () => {
        if (menu) menu.style.display = 'none';
    });

    // Handle item selection
    const items = menu.querySelectorAll('.dropdown-item');
    items.forEach(item => {
        // Simple hover states
        item.addEventListener('mouseenter', () => {
            if (item.style.background !== 'var(--primary)') {
                item.style.background = 'rgba(139, 0, 0, 0.08)';
            }
        });
        item.addEventListener('mouseleave', () => {
            if (item.style.background !== 'var(--primary)') {
                item.style.background = 'none';
            }
        });

        item.addEventListener('click', (e) => {
            e.stopPropagation();
            
            // Update active states in UI
            items.forEach(i => {
                i.style.background = 'none';
                i.style.color = '#1a1a1a';
            });
            item.style.background = 'var(--primary)';
            item.style.color = '#fdfaf5';
            
            const selected = item.dataset.source;
            btn.querySelector('span').innerText = selected === 'ALL' ? 'SOURCE: ALL' : `SOURCE: ${selected}`;
            
            // Re-render map bubbles
            const filterVal = selected === 'ALL' ? null : selected;
            replotMapBubbles(map, mapPoints, entitySourcesMap, filterVal, recentHeadlines);
            
            // Close menu
            menu.style.display = 'none';
        });
    });
}

export function unmountGeoHeatmap() {
    if (window._leafletMap) {
        window._leafletMap.remove();
        window._leafletMap = null;
    }
}

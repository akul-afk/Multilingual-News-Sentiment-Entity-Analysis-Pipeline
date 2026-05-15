// Configuration for the tear effect
const TEAR_RADIUS = 80;  // How far from the corner the tear begins (in pixels)
const TEAR_DEPTH = 35;   // How deeply the corner tears inward
const RESOLUTION = 6;    // Pixel distance between points (lower = more detailed)

export function generateTornPolygons(card) {
    const rect = card.getBoundingClientRect();
    const w = rect.width;
    const h = rect.height;
    
    if (w === 0 || h === 0) return; // Skip hidden elements

    const center = { x: w / 2, y: h / 2 };

    const corners = [
        { x: 0, y: 0 },
        { x: w, y: 0 },
        { x: w, y: h },
        { x: 0, y: h }
    ];

    let ptsBase = [];

    // Trace the perimeter of the rectangle to create the base polygon
    for (let x = 0; x < w; x += RESOLUTION) ptsBase.push({ x, y: 0 });
    for (let y = 0; y < h; y += RESOLUTION) ptsBase.push({ x: w, y });
    for (let x = w; x > 0; x -= RESOLUTION) ptsBase.push({ x, y: h });
    for (let y = h; y > 0; y -= RESOLUTION) ptsBase.push({ x: 0, y });

    let ptsTorn = ptsBase.map(p => {
        let pTorn = { x: p.x, y: p.y };
        let minDist = Infinity;

        // Find distance to the closest corner
        for (let c of corners) {
            let d = Math.hypot(p.x - c.x, p.y - c.y);
            if (d < minDist) minDist = d;
        }

        // If the point is near a corner, mathematically "crunch" it inward
        if (minDist < TEAR_RADIUS) {
            let intensity = Math.pow(1 - (minDist / TEAR_RADIUS), 1.2); 
            let jaggednessX = (Math.random() - 0.5) * 20;
            let jaggednessY = (Math.random() - 0.5) * 20;

            let vx = center.x - p.x;
            let vy = center.y - p.y;
            let len = Math.hypot(vx, vy);

            pTorn.x += (vx / len) * (Math.random() * TEAR_DEPTH) * intensity + (jaggednessX * intensity);
            pTorn.y += (vy / len) * (Math.random() * TEAR_DEPTH) * intensity + (jaggednessY * intensity);
        }
        return pTorn;
    });

    function toPolyString(pts) {
        return pts.map(p => {
            let xPct = Math.max(0, Math.min(100, (p.x / w) * 100));
            let yPct = Math.max(0, Math.min(100, (p.y / h) * 100));
            return `${xPct.toFixed(2)}% ${yPct.toFixed(2)}%`;
        }).join(', ');
    }

    card.style.setProperty('--base-clip', `polygon(${toPolyString(ptsBase)})`);
    card.style.setProperty('--torn-clip', `polygon(${toPolyString(ptsTorn)})`);
}

export function initTornCards() {
    const cards = document.querySelectorAll('.torn-container, .vintage-card');
    cards.forEach(card => generateTornPolygons(card));
}

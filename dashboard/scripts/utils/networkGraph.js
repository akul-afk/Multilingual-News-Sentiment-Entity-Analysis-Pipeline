/**
 * Orbital Relational Network
 * A vintage-styled connection map for entity co-occurrences.
 * Uses a circular layout with bezier links to represent narrative associations.
 */

export function drawNetwork(canvas, coOccurrences) {
    if (!canvas || !coOccurrences || coOccurrences.length === 0) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    let rect = canvas.getBoundingClientRect();
    
    const initCanvas = () => {
        rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
    };
    initCanvas();

    const width = rect.width;
    const height = rect.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.35;

    const links = coOccurrences.slice(0, 15);
    const nodeSet = new Set();
    links.forEach(link => {
        nodeSet.add(link[0]);
        nodeSet.add(link[1]);
    });

    const nodes = Array.from(nodeSet);
    const nodePositions = {};

    nodes.forEach((name, i) => {
        const angle = (i / nodes.length) * Math.PI * 2;
        nodePositions[name] = {
            x: centerX + Math.cos(angle) * radius,
            y: centerY + Math.sin(angle) * radius,
            angle: angle,
            name: name
        };
    });

    let hoveredNode = null;

    function draw() {
        ctx.clearRect(0, 0, width, height);
        
        // Draw orbital guide
        ctx.setLineDash([5, 5]);
        ctx.strokeStyle = 'rgba(90, 60, 30, 0.08)';
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);

        // Draw links
        ctx.lineWidth = 1;
        links.forEach(link => {
            const start = nodePositions[link[0]];
            const end = nodePositions[link[1]];
            const weight = link[2];
            const isHighlighted = hoveredNode === link[0] || hoveredNode === link[1];

            ctx.beginPath();
            ctx.moveTo(start.x, start.y);
            const cpX = centerX + (Math.cos((start.angle + end.angle) / 2) * radius * 0.4);
            const cpY = centerY + (Math.sin((start.angle + end.angle) / 2) * radius * 0.4);
            ctx.quadraticCurveTo(cpX, cpY, end.x, end.y);
            
            ctx.strokeStyle = isHighlighted 
                ? `rgba(139, 0, 0, 0.6)` 
                : `rgba(90, 60, 30, ${Math.min(weight / 50 + 0.05, 0.3)})`;
            ctx.lineWidth = isHighlighted ? 2 : 1;
            ctx.stroke();
        });

        // Draw nodes
        nodes.forEach(name => {
            const pos = nodePositions[name];
            const isHovered = hoveredNode === name;
            
            ctx.beginPath();
            ctx.arc(pos.x, pos.y, isHovered ? 8 : 5, 0, Math.PI * 2);
            ctx.fillStyle = isHovered ? 'var(--primary)' : '#5a3c1e';
            ctx.fill();
            
            if (isHovered) {
                ctx.strokeStyle = 'rgba(139, 0, 0, 0.2)';
                ctx.lineWidth = 4;
                ctx.stroke();
            }

            ctx.font = `${isHovered ? '900' : 'bold'} 11px var(--font-heading)`;
            ctx.fillStyle = isHovered ? 'var(--primary)' : 'var(--text)';
            ctx.textAlign = pos.x > centerX ? 'left' : 'right';
            const offset = pos.x > centerX ? 14 : -14;
            ctx.fillText(name.toUpperCase(), pos.x + offset, pos.y + 4);
        });
    }

    canvas.onmousemove = (e) => {
        const mx = e.offsetX;
        const my = e.offsetY;
        let found = null;
        
        Object.values(nodePositions).forEach(pos => {
            const dist = Math.hypot(pos.x - mx, pos.y - my);
            if (dist < 15) found = pos.name;
        });
        
        if (found !== hoveredNode) {
            hoveredNode = found;
            draw();
            canvas.style.cursor = found ? 'pointer' : 'default';
        }
    };

    canvas.onmouseleave = () => {
        hoveredNode = null;
        draw();
    };

    draw();
}

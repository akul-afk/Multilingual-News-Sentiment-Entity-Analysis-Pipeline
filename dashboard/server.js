const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;

http.createServer((req, res) => {
    if (req.url.startsWith('/auth')) {
        const options = {
            hostname: 'localhost',
            port: 8001,
            path: req.url,
            method: req.method,
            headers: req.headers
        };

        const proxyReq = http.request(options, (proxyRes) => {
            res.writeHead(proxyRes.statusCode, proxyRes.headers);
            proxyRes.pipe(res, { end: true });
        });

        req.pipe(proxyReq, { end: true });
        return;
    }

    let filePath = '.' + req.url;
    if (filePath === './' || filePath.startsWith('./#')) filePath = './index.html';
    // Handle SPA routing - if file doesn't exist, serve index.html
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        filePath = './index.html';
    }

    const extname = path.extname(filePath);
    let contentType = 'text/html';
    switch (extname) {
        case '.js': contentType = 'text/javascript'; break;
        case '.css': contentType = 'text/css'; break;
        case '.json': contentType = 'application/json'; break;
        case '.png': contentType = 'image/png'; break;
        case '.jpg': contentType = 'image/jpg'; break;
        case '.svg': contentType = 'image/svg+xml'; break;
    }

    fs.readFile(filePath, (error, content) => {
        if (error) {
            res.writeHead(500);
            res.end('Error: ' + error.code);
        } else {
            res.writeHead(200, { 'Content-Type': contentType });
            res.end(content, 'utf-8');
        }
    });
}).listen(PORT, () => {
    console.log(`Server running at http://localhost:${PORT}/`);
});

const express = require('express');
const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Create HTTP server for redirection
const httpApp = express();
httpApp.get('*', (req, res) => {
    res.redirect(`https://${req.headers.host}${req.url}`);
});
http.createServer(httpApp).listen(8000, () => {
    console.log('HTTP Server running on port 8000 (redirecting to HTTPS)');
});

// API endpoints
app.post('/api', (req, res) => {
    res.json(req.body);
});

app.get('/api/sample', (req, res) => {
    res.json({
        message: "This is a sample GET response",
        timestamp: new Date().toISOString()
    });
});

app.get('/api/health', (req, res) => {
    res.json({ status: 'healthy' });
});

const options = {
    key: fs.readFileSync(path.join(__dirname, 'certs', 'server.key')),
    cert: fs.readFileSync(path.join(__dirname, 'certs', 'server.crt')),
    minVersion: 'TLSv1.2',
    maxVersion: 'TLSv1.3',
    ciphers: [
        'ECDHE-ECDSA-AES128-GCM-SHA256',
        'ECDHE-RSA-AES128-GCM-SHA256',
        'ECDHE-ECDSA-AES256-GCM-SHA384',
        'ECDHE-RSA-AES256-GCM-SHA384'
    ].join(':')
};

https.createServer(options, app).listen(8443, () => {
    console.log('HTTPS Server running on port 8443');
});

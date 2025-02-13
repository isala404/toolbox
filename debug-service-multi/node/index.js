const express = require('express');
const app = express();

app.use(express.json());

app.get('/healthz', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'nodejs'
    });
});

app.post('/echo', (req, res) => {
    res.json({
        service: 'nodejs',
        echo: req.body
    });
});

const PORT = 8083;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Node.js service listening on port ${PORT}`);
}); 
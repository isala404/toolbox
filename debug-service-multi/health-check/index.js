const express = require('express');
const axios = require('axios');
const app = express();

const services = [
    { name: 'python', url: 'http://localhost:8081/healthz' },
    { name: 'golang', url: 'http://localhost:8082/healthz' },
    { name: 'nodejs', url: 'http://localhost:8083/healthz' },
    { name: 'ballerina', url: 'http://localhost:8084/healthz' },
    { name: 'java', url: 'http://localhost:8085/healthz' }
];

app.get('/health', async (req, res) => {
    try {
        const results = await Promise.all(
            services.map(async (service) => {
                try {
                    await axios.get(service.url);
                    return { service: service.name, status: 'healthy' };
                } catch (error) {
                    return { service: service.name, status: 'unhealthy' };
                }
            })
        );

        const allHealthy = results.every(result => result.status === 'healthy');
        
        res.status(allHealthy ? 200 : 503).json({
            status: allHealthy ? 'healthy' : 'unhealthy',
            services: results
        });
    } catch (error) {
        res.status(500).json({ status: 'error', message: error.message });
    }
});

const PORT = 8080;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Health check service listening on port ${PORT}`);
}); 
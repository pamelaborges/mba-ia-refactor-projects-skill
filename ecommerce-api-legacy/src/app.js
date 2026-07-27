const express = require('express');

const config = require('./config');
const { getDb } = require('./db/connection');
const { initSchema } = require('./db/schema');

const checkoutRoutes = require('./routes/checkoutRoutes');
const adminRoutes = require('./routes/adminRoutes');
const userRoutes = require('./routes/userRoutes');

const app = express();
app.use(express.json());

app.use('/api', checkoutRoutes);
app.use('/api', adminRoutes);
app.use('/api', userRoutes);

async function start() {
    await initSchema(getDb());
    app.listen(config.port, () => {
        console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

start();

module.exports = app;

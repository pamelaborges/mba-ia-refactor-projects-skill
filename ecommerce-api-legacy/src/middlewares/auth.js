const config = require('../config');

function adminRequired(req, res, next) {
    if (config.env === 'production') {
        return res.status(403).json({ error: 'Indisponível em produção' });
    }

    const token = req.headers['x-admin-token'];
    if (!token || token !== config.adminToken) {
        return res.status(401).json({ error: 'Não autorizado' });
    }

    next();
}

module.exports = { adminRequired };

const { getDb } = require('../db/connection');

function create(action) {
    return new Promise((resolve, reject) => {
        getDb().run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action],
            (err) => {
                if (err) return reject(err);
                resolve();
            }
        );
    });
}

module.exports = { create };

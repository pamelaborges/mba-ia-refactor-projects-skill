const { getDb } = require('../db/connection');

function findActiveById(id) {
    return new Promise((resolve, reject) => {
        getDb().get('SELECT * FROM courses WHERE id = ? AND active = 1', [id], (err, row) => {
            if (err) return reject(err);
            resolve(row);
        });
    });
}

function findAll() {
    return new Promise((resolve, reject) => {
        getDb().all('SELECT * FROM courses', [], (err, rows) => {
            if (err) return reject(err);
            resolve(rows);
        });
    });
}

module.exports = { findActiveById, findAll };

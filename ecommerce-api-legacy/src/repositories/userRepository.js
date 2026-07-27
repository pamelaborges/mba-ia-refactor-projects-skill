const { getDb } = require('../db/connection');

function findByEmail(email) {
    return new Promise((resolve, reject) => {
        getDb().get('SELECT id, name, email, pass FROM users WHERE email = ?', [email], (err, row) => {
            if (err) return reject(err);
            resolve(row);
        });
    });
}

function create(name, email, passwordHash) {
    return new Promise((resolve, reject) => {
        getDb().run(
            'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
            [name, email, passwordHash],
            function (err) {
                if (err) return reject(err);
                resolve(this.lastID);
            }
        );
    });
}

function remove(id) {
    return new Promise((resolve, reject) => {
        getDb().run('DELETE FROM users WHERE id = ?', [id], function (err) {
            if (err) return reject(err);
            resolve(this.changes);
        });
    });
}

module.exports = { findByEmail, create, remove };

const { getDb } = require('../db/connection');

function create(enrollmentId, amount, status) {
    return new Promise((resolve, reject) => {
        getDb().run(
            'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
            [enrollmentId, amount, status],
            function (err) {
                if (err) return reject(err);
                resolve(this.lastID);
            }
        );
    });
}

module.exports = { create };

const { getDb } = require('../db/connection');

function create(userId, courseId) {
    return new Promise((resolve, reject) => {
        getDb().run(
            'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)',
            [userId, courseId],
            function (err) {
                if (err) return reject(err);
                resolve(this.lastID);
            }
        );
    });
}

module.exports = { create };

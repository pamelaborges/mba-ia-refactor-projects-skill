const { hashPassword } = require('../services/passwordService');

function initSchema(db) {
    return new Promise((resolve, reject) => {
        db.serialize(() => {
            db.run('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
            db.run('CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)');
            db.run(
                'CREATE TABLE IF NOT EXISTS enrollments (' +
                'id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users(id), course_id INTEGER REFERENCES courses(id))'
            );
            db.run(
                'CREATE TABLE IF NOT EXISTS payments (' +
                'id INTEGER PRIMARY KEY, enrollment_id INTEGER REFERENCES enrollments(id), amount REAL, status TEXT)'
            );
            db.run('CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)');

            db.run(
                'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
                ['Leonan', 'leonan@fullcycle.com.br', hashPassword('123')]
            );
            db.run(
                'INSERT INTO courses (title, price, active) VALUES (?, ?, ?), (?, ?, ?)',
                ['Clean Architecture', 997.00, 1, 'Docker', 497.00, 1]
            );
            db.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
            db.run(
                'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
                [1, 997.00, 'PAID'],
                (err) => {
                    if (err) return reject(err);
                    resolve();
                }
            );
        });
    });
}

module.exports = { initSchema };

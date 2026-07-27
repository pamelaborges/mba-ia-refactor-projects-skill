function runInTransaction(db, work) {
    return new Promise((resolve, reject) => {
        db.run('BEGIN TRANSACTION', (beginErr) => {
            if (beginErr) return reject(beginErr);

            work()
                .then((result) => {
                    db.run('COMMIT', (commitErr) => {
                        if (commitErr) return reject(commitErr);
                        resolve(result);
                    });
                })
                .catch((err) => {
                    db.run('ROLLBACK', () => reject(err));
                });
        });
    });
}

module.exports = { runInTransaction };

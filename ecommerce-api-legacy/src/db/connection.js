const sqlite3 = require('sqlite3').verbose();
const config = require('../config');

let db = null;

function getDb() {
    if (!db) {
        db = new sqlite3.Database(config.dbPath);
        db.run('PRAGMA foreign_keys = ON');
    }
    return db;
}

module.exports = { getDb };

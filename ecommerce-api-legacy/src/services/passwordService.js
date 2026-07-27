const bcrypt = require('bcryptjs');

const SALT_ROUNDS = 10;

function hashPassword(password) {
    return bcrypt.hashSync(password, SALT_ROUNDS);
}

module.exports = { hashPassword };

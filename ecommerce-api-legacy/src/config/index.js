function required(name) {
    const value = process.env[name];
    if (!value) {
        throw new Error(`Variável de ambiente ${name} é obrigatória`);
    }
    return value;
}

module.exports = {
    dbUser: process.env.DB_USER || 'admin_master',
    dbPass: required('DB_PASS'),
    paymentGatewayKey: required('PAYMENT_GATEWAY_KEY'),
    smtpUser: process.env.SMTP_USER || 'no-reply@fullcycle.com.br',
    port: process.env.PORT || 3000,
    adminToken: required('ADMIN_TOKEN'),
    env: process.env.NODE_ENV || 'development',
    dbPath: process.env.DB_PATH || ':memory:',
};

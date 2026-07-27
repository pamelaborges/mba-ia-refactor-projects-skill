const { getDb } = require('../db/connection');
const { runInTransaction } = require('../db/transaction');
const courseRepository = require('../repositories/courseRepository');
const userRepository = require('../repositories/userRepository');
const enrollmentRepository = require('../repositories/enrollmentRepository');
const paymentRepository = require('../repositories/paymentRepository');
const auditLogRepository = require('../repositories/auditLogRepository');
const paymentGateway = require('./paymentGateway');
const passwordService = require('./passwordService');
const { logAndCache } = require('../utils');

class CourseNotFoundError extends Error {}
class PaymentDeniedError extends Error {}

async function checkout({ name, email, password, courseId, cardNumber }) {
    const course = await courseRepository.findActiveById(courseId);
    if (!course) {
        throw new CourseNotFoundError('Curso não encontrado');
    }

    const existingUser = await userRepository.findByEmail(email);
    let userId;
    if (existingUser) {
        userId = existingUser.id;
    } else {
        const passwordHash = passwordService.hashPassword(password || '123456');
        userId = await userRepository.create(name, email, passwordHash);
    }

    const status = paymentGateway.charge(cardNumber);
    if (status === 'DENIED') {
        throw new PaymentDeniedError('Pagamento recusado');
    }

    const db = getDb();
    const enrollmentId = await runInTransaction(db, async () => {
        const enrId = await enrollmentRepository.create(userId, courseId);
        await paymentRepository.create(enrId, course.price, status);
        await auditLogRepository.create(`Checkout curso ${courseId} por ${userId}`);
        return enrId;
    });

    logAndCache(`last_checkout_${userId}`, course.title);
    return { enrollmentId, userId };
}

module.exports = { checkout, CourseNotFoundError, PaymentDeniedError };

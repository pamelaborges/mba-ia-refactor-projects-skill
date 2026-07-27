const checkoutService = require('../services/checkoutService');

async function checkout(req, res) {
    const name = req.body.usr;
    const email = req.body.eml;
    const password = req.body.pwd;
    const courseId = req.body.c_id;
    const cardNumber = req.body.card;

    if (!name || !email || !courseId || !cardNumber) {
        return res.status(400).send('Bad Request');
    }

    try {
        const { enrollmentId } = await checkoutService.checkout({ name, email, password, courseId, cardNumber });
        return res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    } catch (err) {
        if (err instanceof checkoutService.CourseNotFoundError) {
            return res.status(404).send('Curso não encontrado');
        }
        if (err instanceof checkoutService.PaymentDeniedError) {
            return res.status(400).send('Pagamento recusado');
        }
        console.error('Erro no checkout:', err);
        return res.status(500).send('Erro ao processar checkout');
    }
}

module.exports = { checkout };

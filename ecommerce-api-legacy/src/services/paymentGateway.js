const VISA_TEST_PREFIX = '4';

function charge(cardNumber) {
    return cardNumber.startsWith(VISA_TEST_PREFIX) ? 'PAID' : 'DENIED';
}

module.exports = { charge };

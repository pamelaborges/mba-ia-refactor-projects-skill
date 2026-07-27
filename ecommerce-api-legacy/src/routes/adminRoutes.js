const express = require('express');

const adminController = require('../controllers/adminController');
const { adminRequired } = require('../middlewares/auth');

const router = express.Router();

router.get('/admin/financial-report', adminRequired, adminController.financialReport);

module.exports = router;

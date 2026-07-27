const express = require('express');

const userController = require('../controllers/userController');
const { adminRequired } = require('../middlewares/auth');

const router = express.Router();

router.delete('/users/:id', adminRequired, userController.deleteUser);

module.exports = router;

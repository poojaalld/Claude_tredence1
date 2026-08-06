const express = require('express');
const controller = require('../controllers/productsController');

const router = express.Router();

router.get('/products', controller.listProducts);
router.get('/products/:id', controller.getProductById);
router.get('/collections', controller.listCollections);

module.exports = router;

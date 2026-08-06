const inventoryService = require('../services/inventoryService');

function listProducts(req, res) {
  const products = inventoryService.listProducts(req.query);
  res.json({
    count: products.length,
    results: products
  });
}

function getProductById(req, res) {
  const product = inventoryService.getProductById(req.params.id);
  if (!product) {
    return res.status(404).json({ error: 'Product not found in catalog.' });
  }

  res.json(product);
}

function listCollections(req, res) {
  const collections = inventoryService.listCollections();
  res.json(collections);
}

module.exports = {
  listProducts,
  getProductById,
  listCollections
};

const catalog = require('../data/catalog.json');

function listProducts(filters = {}) {
  let items = catalog.products;

  if (filters.category) {
    items = items.filter((p) =>
      p.category.toLowerCase() === filters.category.toLowerCase()
    );
  }

  if (filters.q) {
    const term = filters.q.toLowerCase();
    items = items.filter(
      (p) =>
        p.name.toLowerCase().includes(term) ||
        p.tags.some((tag) => tag.includes(term))
    );
  }

  return items.map((product) => ({
    id: product.id,
    name: product.name,
    price: product.price,
    category: product.category,
    inventory: product.inventory
  }));
}

function getProductById(id) {
  return catalog.products.find((product) => product.id === id);
}

function listCollections() {
  const apparel = catalog.products.filter((p) => p.category === 'Apparel');
  const footwear = catalog.products.filter((p) => p.category === 'Footwear');

  return [
    {
      name: 'Apparel Highlights',
      items: apparel.map((p) => ({ id: p.id, name: p.name }))
    },
    {
      name: 'Footwear Spotlight',
      items: footwear.map((p) => ({ id: p.id, name: p.name }))
    }
  ];
}

module.exports = {
  listProducts,
  getProductById,
  listCollections
};

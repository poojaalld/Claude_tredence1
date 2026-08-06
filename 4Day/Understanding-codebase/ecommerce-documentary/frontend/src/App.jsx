import { useEffect, useMemo, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:4000/api';

const samplePrompts = {
  folder: 'Survey `frontend/src/components` and explain how the filters, grid, and CTA bar work together to present catalog items.',
  func: 'Read `backend/src/services/inventoryService.js` and summarize how product availability and stock alerts are calculated.'
};

function App() {
  const [products, setProducts] = useState([]);
  const [collections, setCollections] = useState([]);
  const [category, setCategory] = useState('');
  const [query, setQuery] = useState('');
  const [status, setStatus] = useState('Loading catalog...');

  useEffect(() => {
    const fetchCatalog = async () => {
      setStatus('Loading catalog...');
      const params = new URLSearchParams();
      if (category) params.set('category', category);
      if (query) params.set('q', query);

      const url = `${API_BASE}/products?${params.toString()}`;
      const response = await fetch(url);
      if (!response.ok) {
        setStatus('Unable to load catalog.');
        return;
      }

      const payload = await response.json();
      setProducts(payload.results || []);
      setStatus(`${(payload.count || 0)} catalog items loaded`);
    };

    fetchCatalog();
  }, [category, query]);

  useEffect(() => {
    fetch(`${API_BASE}/collections`)
      .then((res) => res.json())
      .then(setCollections)
      .catch(() => {});
  }, []);

  const inventorySummary = useMemo(() => {
    const total = products.length;
    const inventory = products.reduce((sum, item) => sum + item.inventory, 0);
    return { total, inventory };
  }, [products]);

  return (
    <div className="page">
      <header className="hero">
        <p className="eyebrow">Module 4 · Codebase Understanding</p>
        <h1>E-Commerce Documentary Lab</h1>
        <p className="lede">
          Practice folder-level and function-level summaries while the React UI
          narrates how the backend catalog, filters, and documentation panels
          connect.
        </p>
      </header>

      <section className="panel">
        <div className="panel-header">
          <h2>Catalog snapshot</h2>
          <span>{status}</span>
        </div>
        <div className="filters">
          <label>
            Category
            <select
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            >
              <option value="">All</option>
              <option value="Apparel">Apparel</option>
              <option value="Footwear">Footwear</option>
            </select>
          </label>
          <label>
            Keyword
            <input
              value={query}
              placeholder="search tags or name"
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
        </div>
        <div className="grid">
          {products.map((product) => (
            <article key={product.id} className="card">
              <h3>{product.name}</h3>
              <p className="meta">
                {product.category} · Inventory: {product.inventory}
              </p>
              <p className="price">${product.price}</p>
            </article>
          ))}
          {!products.length && <p>No catalog results</p>}
        </div>
        <div className="summary">
          <strong>Total items:</strong> {inventorySummary.total}{' '}
          <span className="spacer">|</span>
          <strong>Total inventory:</strong> {inventorySummary.inventory}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Collections (for documentary highlights)</h2>
        </div>
        <div className="collections">
          {collections.map((collection) => (
            <div key={collection.name} className="collection">
              <h3>{collection.name}</h3>
              <ul>
                {collection.items.map((item) => (
                  <li key={item.id}>{item.name}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <p className="note">
          Use Claude to ask, “How are these collections created from the same
          catalog data?” vs. “What do the routes/products controller and
          inventoryService do to surface these lists?”
        </p>
      </section>

      <section className="panel">
        <h2>Prompt strategy log</h2>
        <div className="prompt-grid">
          <article>
            <h3>Function-level</h3>
            <p>{samplePrompts.func}</p>
            <p>Result: Focused explanation tied to `inventoryService.js`.</p>
          </article>
          <article>
            <h3>Folder-level</h3>
            <p>{samplePrompts.folder}</p>
            <p>
              Result: Broad narrative that mentions filters, grids, and CTA
              panels (use `docs/Documentary-template.md` to capture the callout).
            </p>
          </article>
        </div>
        <div className="documentary-note">
          <p>
            After capturing these summaries, prompt Claude to write README
            sections—Overview, API, and Running instructions—then validate the
            statements against the source files listed in `docs/prompt-strategies.md`.
          </p>
        </div>
      </section>
    </div>
  );
}

export default App;

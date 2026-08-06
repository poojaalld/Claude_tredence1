const express = require('express');
const cors = require('cors');
const productsRouter = require('./routes/products');

const app = express();

app.use(cors());
app.use(express.json());

app.use('/api', productsRouter);

app.use((req, res) => {
  res.status(404).json({
    error: 'This route is not defined. Follow the API contract in docs/prompt-strategies.md.'
  });
});

const port = process.env.PORT || 4000;
app.listen(port, () => {
  console.log(`Marketplace API listening on http://localhost:${port}`);
});

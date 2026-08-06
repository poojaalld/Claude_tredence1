const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 5000;

app.use(cors());
app.use(express.json());

function calculateEmi(principal, annualRate, tenureMonths) {
  const monthlyRate = annualRate / 12 / 100;

  if (monthlyRate === 0) {
    const emi = principal / tenureMonths;
    return {
      emi,
      totalPayment: principal,
      totalInterest: 0,
    };
  }

  const factor = Math.pow(1 + monthlyRate, tenureMonths);
  const emi = (principal * monthlyRate * factor) / (factor - 1);
  const totalPayment = emi * tenureMonths;
  const totalInterest = totalPayment - principal;

  return { emi, totalPayment, totalInterest };
}

app.post('/api/emi', (req, res) => {
  const { principal, rate, tenureMonths } = req.body;

  if (
    typeof principal !== 'number' || principal <= 0 ||
    typeof rate !== 'number' || rate < 0 ||
    typeof tenureMonths !== 'number' || tenureMonths <= 0
  ) {
    return res.status(400).json({ error: 'Invalid input. principal and tenureMonths must be positive numbers, rate must be non-negative.' });
  }

  const result = calculateEmi(principal, rate, tenureMonths);
  res.json(result);
});

app.listen(PORT, () => {
  console.log(`EMI backend running on http://localhost:${PORT}`);
});

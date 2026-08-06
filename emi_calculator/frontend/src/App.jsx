import { useState } from 'react'
import './App.css'

const API_URL = 'http://localhost:5000/api/emi'

function App() {
  const [principal, setPrincipal] = useState('')
  const [rate, setRate] = useState('')
  const [years, setYears] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const formatCurrency = (value) =>
    value.toLocaleString('en-IN', { maximumFractionDigits: 2, minimumFractionDigits: 2 })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setResult(null)

    const principalNum = parseFloat(principal)
    const rateNum = parseFloat(rate)
    const yearsNum = parseFloat(years)

    if (!principalNum || principalNum <= 0) {
      setError('Please enter a valid principal amount.')
      return
    }
    if (rateNum === undefined || isNaN(rateNum) || rateNum < 0) {
      setError('Please enter a valid interest rate.')
      return
    }
    if (!yearsNum || yearsNum <= 0) {
      setError('Please enter a valid duration.')
      return
    }

    setLoading(true)
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          principal: principalNum,
          rate: rateNum,
          tenureMonths: Math.round(yearsNum * 12),
        }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.error || 'Something went wrong.')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message || 'Could not reach the server. Is the backend running?')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setPrincipal('')
    setRate('')
    setYears('')
    setResult(null)
    setError('')
  }

  return (
    <div className="page">
      <div className="card">
        <h1>EMI Calculator</h1>
        <p className="subtitle">Estimate your monthly loan installment</p>

        <form onSubmit={handleSubmit} className="form">
          <label>
            Principal Amount
            <input
              type="number"
              placeholder="e.g. 500000"
              value={principal}
              onChange={(e) => setPrincipal(e.target.value)}
              min="0"
              step="any"
            />
          </label>

          <label>
            Rate of Interest (% per annum)
            <input
              type="number"
              placeholder="e.g. 8.5"
              value={rate}
              onChange={(e) => setRate(e.target.value)}
              min="0"
              step="any"
            />
          </label>

          <label>
            Loan Duration (years)
            <input
              type="number"
              placeholder="e.g. 5"
              value={years}
              onChange={(e) => setYears(e.target.value)}
              min="0"
              step="any"
            />
          </label>

          {error && <div className="error">{error}</div>}

          <div className="button-row">
            <button type="submit" className="btn primary" disabled={loading}>
              {loading ? 'Calculating…' : 'Calculate EMI'}
            </button>
            <button type="button" className="btn secondary" onClick={handleReset}>
              Reset
            </button>
          </div>
        </form>

        {result && (
          <div className="results">
            <div className="result-item highlight">
              <span>Monthly EMI</span>
              <strong>₹ {formatCurrency(result.emi)}</strong>
            </div>
            <div className="result-item">
              <span>Total Interest</span>
              <strong>₹ {formatCurrency(result.totalInterest)}</strong>
            </div>
            <div className="result-item">
              <span>Total Payment</span>
              <strong>₹ {formatCurrency(result.totalPayment)}</strong>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App

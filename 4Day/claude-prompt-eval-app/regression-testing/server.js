require('dotenv').config({ path: require('path').join(__dirname, '..', '.env') });

const fs = require('fs');
const path = require('path');
const express = require('express');
const Anthropic = require('@anthropic-ai/sdk');

const PORT = process.env.REGRESSION_PORT || 4100;
const MODEL = 'claude-haiku-4-5-20251001';
const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const datasetPath = path.join(__dirname, '..', 'data', 'golden_dataset.json');
const promptPath = path.join(__dirname, '..', 'prompts', 'prompt_v1.txt');
const baselinePath = path.join(__dirname, 'baseline.json');

const dataset = JSON.parse(fs.readFileSync(datasetPath, 'utf-8'));
const prompt = fs.readFileSync(promptPath, 'utf-8');

function fillTemplate(template, testCase) {
  return template.replace(/{{(\w+)}}/g, (_, key) => testCase[key] ?? '');
}

function extractDecision(text) {
  const structured = text.match(/Decision:\s*(Approve|Reject)/i);
  if (structured) return structured[1].charAt(0).toUpperCase() + structured[1].slice(1).toLowerCase();
  if (/\bapprove/i.test(text)) return 'Approve';
  if (/\breject/i.test(text)) return 'Reject';
  return 'Unclear';
}

async function runPrompt(template, testCase) {
  const response = await anthropic.messages.create({
    model: MODEL,
    max_tokens: 300,
    messages: [{ role: 'user', content: fillTemplate(template, testCase) }],
  });
  const raw = response.content.map((block) => block.text || '').join('');
  const decision = extractDecision(raw);
  return { raw, decision, expected: testCase.expected };
}

function loadBaseline() {
  if (!fs.existsSync(baselinePath)) return [];
  return JSON.parse(fs.readFileSync(baselinePath, 'utf-8'));
}

function saveBaseline(results) {
  fs.writeFileSync(baselinePath, JSON.stringify(results, null, 2));
}

const app = express();
app.use(express.json());

app.get('/api/health', (_req, res) => res.json({ ok: true }));

app.all('/api/regression', async (req, res) => {
  if (req.method === 'GET') {
    return res.json({
      message: 'Use POST /api/regression to run a regression check.',
      datasetCount: dataset.length,
      baselineExists: fs.existsSync(baselinePath),
    });
  }

  try {
    const currentResults = [];
    for (const testCase of dataset) {
      const result = await runPrompt(prompt, testCase);
      currentResults.push({ ...testCase, result });
    }

    const baseline = loadBaseline();
    const drift = currentResults.map((item, index) => {
      const prev = baseline[index];
      const currentDecision = item.result.decision;
      const previousDecision = prev?.result?.decision;
      return {
        id: item.id,
        expected: item.expected,
        currentDecision,
        previousDecision,
        drifted: previousDecision && currentDecision !== previousDecision,
      };
    });

    saveBaseline(currentResults);
    res.json({ baselineCount: baseline.length, currentCount: currentResults.length, drift });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`Regression testing app running at http://localhost:${PORT}`);
});

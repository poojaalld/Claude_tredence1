require("dotenv").config();

const fs = require("fs");
const path = require("path");
const express = require("express");
const Anthropic = require("@anthropic-ai/sdk");

const PORT = process.env.PORT || 4000;
const MODEL = "claude-haiku-4-5-20251001";

const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const dataset = JSON.parse(fs.readFileSync(path.join(__dirname, "data", "golden_dataset.json"), "utf-8"));
const promptV1 = fs.readFileSync(path.join(__dirname, "prompts", "prompt_v1.txt"), "utf-8");
const promptV2 = fs.readFileSync(path.join(__dirname, "prompts", "prompt_v2.txt"), "utf-8");

function fillTemplate(template, testCase) {
  return template.replace(/{{(\w+)}}/g, (_, key) => testCase[key] ?? "");
}

function extractDecision(text) {
  const structured = text.match(/Decision:\s*(Approve|Reject)/i);
  if (structured) {
    const word = structured[1].toLowerCase();
    return word[0].toUpperCase() + word.slice(1);
  }
  if (/\bapprove/i.test(text)) return "Approve";
  if (/\breject/i.test(text)) return "Reject";
  return "Unclear";
}

async function runPrompt(template, testCase) {
  const response = await anthropic.messages.create({
    model: MODEL,
    max_tokens: 300,
    messages: [{ role: "user", content: fillTemplate(template, testCase) }],
  });
  const raw = response.content.map((block) => block.text || "").join("");
  const decision = extractDecision(raw);
  return { raw, decision, pass: decision === testCase.expected };
}

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

app.get("/api/dataset", (_req, res) => res.json(dataset));

app.get("/api/prompts", (_req, res) => res.json({ v1: promptV1, v2: promptV2 }));

app.get("/api/regression", (_req, res) => {
  res.json({
    message: "Use POST /api/regression to run a regression check.",
    datasetCount: dataset.length,
  });
});

app.post("/api/regression", async (_req, res) => {
  try {
    const results = [];
    for (const testCase of dataset) {
      const result = await runPrompt(promptV1, testCase);
      results.push({ ...testCase, result });
    }

    res.json({ model: MODEL, results });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

app.post("/api/run", async (_req, res) => {
  try {
    const results = [];
    for (const testCase of dataset) {
      const [v1, v2] = await Promise.all([
        runPrompt(promptV1, testCase),
        runPrompt(promptV2, testCase),
      ]);
      results.push({ ...testCase, v1, v2 });
    }
    res.json({ model: MODEL, results });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`Claude prompt-eval app running at http://localhost:${PORT}`);
});

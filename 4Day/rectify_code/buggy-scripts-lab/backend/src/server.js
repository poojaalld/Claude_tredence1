const express = require("express");
const cors = require("cors");

const app = express();
app.use(cors());
app.use(express.json());

const scriptCatalog = [
  {
    id: "calculateBonus",
    title: "calculateBonus.js",
    description:
      "ReferenceError: BONUS_RATES is accessed before initialization because the call to calculateBonus happens before the constant is defined.",
    command: "node scripts/calculateBonus.js",
    errorSummary: "ReferenceError: Cannot access 'BONUS_RATES' before initialization",
    fixMessage:
      "Move the BONUS_RATES definition before the first call or add a default guard so that the constant is initialized before usage.",
    patchPreview: `--- scripts/calculateBonus.js
+++ scripts/calculateBonus.js
@@
-const salary = Number(process.argv[2] || 50000);
-const performance = process.argv[3] || "medium";
-
-const payout = calculateBonus(salary, performance);
-console.log(\`Calculated bonus for \${performance} performance: \${payout}\`);
-
-const BONUS_RATES = {
-  high: 0.15,
-  medium: 0.08,
-  low: 0.04
-};
-
function calculateBonus(amount, level) {
  return amount * BONUS_RATES[level];
}
+const BONUS_RATES = {
+  high: 0.15,
+  medium: 0.08,
+  low: 0.04
+};

const salary = Number(process.argv[2] || 50000);
const performance = process.argv[3] || "medium";

const payout = calculateBonus(salary, performance);
console.log(\`Calculated bonus for \${performance} performance: \${payout}\`);

function calculateBonus(amount, level) {
  return amount * BONUS_RATES[level];
}`,
  },
  {
    id: "validateUser",
    title: "validateUser.js",
    description:
      "TypeError because the script assumes `user` exists before checking the CLI payload, so `user.roles` is accessed on undefined.",
    command: "node scripts/validateUser.js",
    errorSummary: "TypeError: Cannot read properties of undefined (reading 'roles')",
    fixMessage:
      "Check for a payload before iterating roles and default to an empty array when the data is missing or malformed.",
    patchPreview: `--- scripts/validateUser.js
+++ scripts/validateUser.js
@@
-const userPayload = process.argv[2];
-const user = userPayload ? JSON.parse(userPayload) : undefined;
-
-function describeAccess(u) {
-  return u.roles.map((role) => role.toUpperCase()).join(", ");
-}
-
-console.log("User access:", describeAccess(user));
+const userPayload = process.argv[2];
+const user = userPayload ? JSON.parse(userPayload) : undefined;
+
+function describeAccess(u) {
+  const roles = u?.roles ?? [];
+  return roles.map((role) => role.toUpperCase()).join(", ");
+}
+
+if (!user) {
+  console.log("No user payload supplied. Provide a JSON object with a 'roles' array.");
+} else {
+  console.log("User access:", describeAccess(user));
+}`,
  },
  {
    id: "emailScheduler",
    title: "emailScheduler.js",
    description:
      "SyntaxError arises because `await` is used inside `scheduleEmail` without marking it as `async`.",
    command: "node scripts/emailScheduler.js",
    errorSummary: "SyntaxError: await is only valid in async functions",
    fixMessage: "Mark `scheduleEmail` as `async` so the `await sendEmail` expression is valid.",
    patchPreview: `--- scripts/emailScheduler.js
+++ scripts/emailScheduler.js
@@
-function scheduleEmail(message) {
+async function scheduleEmail(message) {
   console.log("Queueing message:", message);
   await sendEmail(message);
 }
 `,
  },
  {
    id: "configMerge",
    title: "configMerge.js",
    description:
      "ReferenceError occurs because the script spreads `overrides` without defining it when the caller doesn’t supply overrides.",
    command: "node scripts/configMerge.js",
    errorSummary: "ReferenceError: overrides is not defined",
    fixMessage: "Provide a fallback object (e.g. read from environment) before merging to prevent the error.",
    patchPreview: `--- scripts/configMerge.js
+++ scripts/configMerge.js
@@
-const defaults = {
-  host: "api.example.com",
-  retries: 3,
-  timeout: 5000
-};
-
-const consolidated = { ...defaults, ...overrides };
-console.log("Merged configuration:", consolidated);
+const defaults = {
+  host: "api.example.com",
+  retries: 3,
+  timeout: 5000
+};
+
+const overrides = process.env.CONFIG_OVERRIDES ? JSON.parse(process.env.CONFIG_OVERRIDES) : {};
+
+const consolidated = { ...defaults, ...overrides };
+console.log("Merged configuration:", consolidated);
`,
  },
  {
    id: "retryHandler",
    title: "retryHandler.js",
    description:
      "RangeError due to constructing an array with a negative length; the CLI default is -2 when no argument is supplied.",
    command: "node scripts/retryHandler.js",
    errorSummary: "RangeError: Invalid array length",
    fixMessage: "Clamp `maxRetries` to a positive integer before passing it to `new Array`.",
    patchPreview: `--- scripts/retryHandler.js
+++ scripts/retryHandler.js
@@
-const maxRetries = Number(process.argv[2]) || -2;
-const windows = new Array(maxRetries).fill(1000);
-console.log("Retry windows:", windows);
+const maxRetries = Math.max(1, Number(process.argv[2]) || 3);
+const windows = new Array(maxRetries).fill(1000);
+console.log("Retry windows:", windows);
`,
  }
];

app.get("/scripts", (req, res) => {
  const catalogView = scriptCatalog.map(({ id, title, description, command }) => ({
    id,
    title,
    description,
    command
  }));
  res.json(catalogView);
});

app.post("/diagnose-script", (req, res) => {
  const { scriptId } = req.body || {};
  const entry = scriptCatalog.find((script) => script.id === scriptId);
  if (!entry) {
    return res.status(404).json({ message: "Script definition not found" });
  }

  const payload = {
    scriptTitle: entry.title,
    errorSummary: entry.errorSummary,
    fixMessage: entry.fixMessage,
    patchPreview: entry.patchPreview
  };
  return res.json(payload);
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Buggy scripts diagnostics API listening on port ${PORT}`);
});

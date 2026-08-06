const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:5000";

export async function fetchScripts() {
  const response = await fetch(`${API_URL}/scripts`);
  if (!response.ok) {
    throw new Error("Failed to load script catalog");
  }
  return response.json();
}

export async function analyzeScript(scriptId) {
  const response = await fetch(`${API_URL}/diagnose-script`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ scriptId })
  });

  if (!response.ok) {
    throw new Error("Diagnostics endpoint returned an error");
  }

  return response.json();
}

import { useEffect, useMemo, useState } from "react";
import { analyzeScript, fetchScripts } from "./scriptsApi";

function App() {
  const [scripts, setScripts] = useState([]);
  const [selectedScript, setSelectedScript] = useState("");
  const [diagnostic, setDiagnostic] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchScripts()
      .then((data) => {
        setScripts(data);
        if (data.length) {
          setSelectedScript(data[0].id);
        }
      })
      .catch(() => {
        setError("Backend is unreachable. Start the Buggy Scripts backend on port 5000.");
      });
  }, []);

  const activeScript = useMemo(() => {
    return scripts.find((script) => script.id === selectedScript);
  }, [scripts, selectedScript]);

  const handleAnalyze = async () => {
    if (!selectedScript) return;
    setLoading(true);
    setError("");
    setDiagnostic(null);
    try {
      const payload = await analyzeScript(selectedScript);
      setDiagnostic(payload);
    } catch (err) {
      setError("Unable to run the diagnostics request. Check that the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <header>
        <p className="eyebrow">Module 3 • Debugging with Claude</p>
        <h1>Buggy Scripts Rescue</h1>
        <p>
          Select one of the intentionally broken Node scripts, send its failure to Claude, and compare the suggested
          patch with your own fix.
        </p>
      </header>

      <section className="script-picker">
        <label htmlFor="script-select">Choose a script to analyze</label>
        <div className="picker-row">
          <select
            id="script-select"
            value={selectedScript}
            onChange={(event) => setSelectedScript(event.target.value)}
          >
            {scripts.map((script) => (
              <option key={script.id} value={script.id}>
                {script.title}
              </option>
            ))}
          </select>
          <button type="button" onClick={handleAnalyze} disabled={loading || !selectedScript}>
            {loading ? "Requesting fix…" : "Ask Claude for a fix"}
          </button>
        </div>
        {activeScript && (
          <div className="script-description">
            <p>{activeScript.description}</p>
            <code>{activeScript.command}</code>
          </div>
        )}
      </section>

      {error && <p className="status error">{error}</p>}

      {diagnostic && (
        <section className="diagnostic-card">
          <div className="diagnostic-detail">
            <strong>Script</strong>
            <p>{diagnostic.scriptTitle}</p>
          </div>
          <div className="diagnostic-detail">
            <strong>Error observed</strong>
            <p>{diagnostic.errorSummary}</p>
          </div>
          <div className="diagnostic-detail">
            <strong>Suggested fix</strong>
            <p>{diagnostic.fixMessage}</p>
          </div>
          <div className="patch-preview">
            <strong>Patch preview</strong>
            <pre>{diagnostic.patchPreview}</pre>
          </div>
        </section>
      )}
    </div>
  );
}

export default App;

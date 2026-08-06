import { useState } from "react";

const AUTH_ENDPOINT = "http://localhost:5000/login";

export default function App() {
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setStatus("Signing in...");
    setIsSubmitting(true);

    try {
      const response = await fetch(AUTH_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ userId, password })
      });
      const payload = await response.json();
      if (response.ok) {
        setStatus(payload.message);
      } else {
        setStatus(payload.error || "Sign in failed.");
      }
    } catch (error) {
      setStatus("Unable to reach the backend.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="panel">
      <h1>Authorization demo</h1>
      <p>Try learner/pass123 or demo/claude to see the success prompt.</p>
      <form onSubmit={handleSubmit} className="form">
        <label>
          User ID
          <input
            value={userId}
            placeholder="learner"
            onChange={(event) => setUserId(event.target.value)}
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            placeholder="pass123"
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
      {status && <div className="status">{status}</div>}
    </main>
  );
}

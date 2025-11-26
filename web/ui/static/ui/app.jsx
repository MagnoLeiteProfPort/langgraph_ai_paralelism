const { useState } = React;

function genderBadge(gender) {
  const g = (gender || "none").toLowerCase();
  if (g === "male") {
    return <span className="badge badge-male">Male</span>;
  }
  if (g === "female") {
    return <span className="badge badge-female">Female</span>;
  }
  return <span className="badge badge-none">None</span>;
}

function consistentBadge(consistent) {
  if (consistent) {
    return <span className="badge badge-consistent">Consistent</span>;
  }
  return <span className="badge badge-inconsistent">Inconsistent</span>;
}

function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      // FastAPI is exposed on localhost:8001 in docker-compose
      const resp = await fetch("http://localhost:8001/generate-outfit", {
        method: "POST",
      });

      if (!resp.ok) {
        throw new Error(`API error: ${resp.status}`);
      }

      const data = await resp.json();
      setResult(data);
    } catch (err) {
      console.error(err);
      setError("Failed to generate outfit. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h1>Outfit Gender Workflow</h1>
      <p className="subtitle">
        Generates head, torso, and leg clothing in parallel and validates gender
        consistency using a LangGraph + FastAPI backend.
      </p>

      <button onClick={handleGenerate} disabled={loading}>
        {loading ? "Generating..." : "Generate Outfit"}
      </button>

      {error && (
        <p style={{ color: "#fca5a5", marginTop: "1rem", fontSize: "0.85rem" }}>
          {error}
        </p>
      )}

      {result && (
        <div className="result">
          <div className="row">
            <span className="label">Overall gender</span>
            <span className="value">{genderBadge(result.gender)}</span>
          </div>
          <div className="row">
            <span className="label">Consistency</span>
            <span className="value">
              {consistentBadge(result.consistent)} (attempts:{" "}
              {result.attempts != null ? result.attempts : "?"})
            </span>
          </div>

          <div style={{ marginTop: "1rem" }}>
            <div className="row">
              <span className="label">Head</span>
              <span className="value">
                {result.head_item || "—"} &nbsp;
                {genderBadge(result.head_gender)}
              </span>
            </div>
            <div className="row">
              <span className="label">Torso</span>
              <span className="value">
                {result.torso_item || "—"} &nbsp;
                {genderBadge(result.torso_gender)}
              </span>
            </div>
            <div className="row">
              <span className="label">Legs</span>
              <span className="value">
                {result.leg_item || "—"} &nbsp;
                {genderBadge(result.leg_gender)}
              </span>
            </div>
          </div>

          <p className="small">
            The workflow diagram is exported as <strong>workflow_graph.png</strong> in
            your project root (inside the API container volume).
          </p>
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);

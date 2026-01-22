import { useState } from "react";

type Props = {
  code: string;
};

export default function CodeRunner({ code }: Props) {
  const [output, setOutput] = useState<string>("");

  const run = () => {
    const worker = new Worker("/sandbox-worker.js");

    worker.onmessage = (e) => {
      setOutput(e.data.output || e.data.error);
      worker.terminate();
    };

    worker.postMessage(code);
  };

  return (
    <div style={{
      marginTop: 12,
      padding: 12,
      background: "#020617",
      borderRadius: 8
    }}>
      <pre style={{
        background: "#020617",
        color: "#e5e7eb",
        padding: 12,
        borderRadius: 6,
        overflowX: "auto"
      }}>
        {code}
      </pre>

      <button
        onClick={run}
        style={{
          marginTop: 8,
          background: "#16a34a",
          color: "white",
          border: "none",
          padding: "6px 14px",
          borderRadius: 6
        }}
      >
        ▶ Run Python
      </button>

      {output && (
        <pre style={{
          marginTop: 8,
          background: "#020617",
          padding: 10,
          borderRadius: 6,
          color: "#a7f3d0"
        }}>
          {output}
        </pre>
      )}
    </div>
  );
}

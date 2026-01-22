import { useState } from "react";
import { api } from "../api/client";
import MessageBubble from "./MessageBubble";
import CodeRunner from "./CodeRunner";
import { parseLLMResponse } from "../utils/parseResponse";

type Message = {
  role: "user" | "agent";
  text: string;
};

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const res = await api.post("/ask", { query: input });

      const agentMessage: Message = {
        role: "agent",
        text: res.data.answer,
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "agent",
          text: "❌ Backend error. Is the server running?",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        padding: 20,
      }}
    >
      {/* Chat messages */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          paddingRight: 8,
        }}
      >
        {messages.map((m, i) => {
          if (m.role === "agent") {
            const parsed = parseLLMResponse(m.text);

            return (
              <div key={i}>
                {parsed.explanation && (
                  <MessageBubble
                    role="agent"
                    text={parsed.explanation}
                  />
                )}

                {parsed.code && (
                  <CodeRunner code={parsed.code} />
                )}
              </div>
            );
          }

          return (
            <MessageBubble
              key={i}
              role="user"
              text={m.text}
            />
          );
        })}

        {loading && (
          <MessageBubble role="agent" text="Thinking…" />
        )}
      </div>

      {/* Input box */}
      <div
        style={{
          display: "flex",
          gap: 8,
          marginTop: 12,
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask something about the PDF…"
          style={{
            flex: 1,
            padding: 10,
            borderRadius: 6,
            border: "1px solid #334155",
            background: "#020617",
            color: "white",
          }}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />

        <button
          onClick={send}
          disabled={loading}
          style={{
            padding: "0 18px",
            borderRadius: 6,
            background: "#2563eb",
            color: "white",
            border: "none",
            opacity: loading ? 0.6 : 1,
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
}

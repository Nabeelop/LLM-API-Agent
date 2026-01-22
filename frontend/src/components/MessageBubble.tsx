type Props = {
  role: "user" | "agent";
  text: string;
};

export default function MessageBubble({ role, text }: Props) {
  const isUser = role === "user";

  return (
    <div style={{
      display: "flex",
      justifyContent: isUser ? "flex-end" : "flex-start",
      marginBottom: 12
    }}>
      <div style={{
        maxWidth: "70%",
        padding: "10px 14px",
        borderRadius: 10,
        background: isUser ? "#2563eb" : "#1e293b",
        color: "white",
        whiteSpace: "pre-wrap",
        lineHeight: 1.5
      }}>
        {text}
      </div>
    </div>
  );
}

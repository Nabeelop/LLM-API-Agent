export function formatSandboxOutput(raw: unknown): string {
  if (raw === null || raw === undefined) {
    return "";
  }

  let text: string;

  // 1. If sandbox sends an object, extract fields safely
  if (typeof raw === "object") {
    const obj = raw as Record<string, unknown>;
    if (typeof obj.output === "string") {
      text = obj.output;
    } else if (typeof obj.error === "string") {
      text = obj.error;
    } else {
      // Fallback: stringify unknown object
      text = JSON.stringify(obj, null, 2);
    }
  } else {
    text = String(raw);
  }

  // 2. Remove surrounding quotes ONLY if they wrap the entire string
  if (
    (text.startsWith('"') && text.endsWith('"')) ||
    (text.startsWith("'") && text.endsWith("'"))
  ) {
    text = text.slice(1, -1);
  }

  // 3. Normalize newlines (handles \\n, \\r\\n)
  text = text
    .replace(/\\r\\n/g, "\n")
    .replace(/\\n/g, "\n")
    .replace(/\r\n/g, "\n");

  // 4. Normalize tabs
  text = text.replace(/\\t/g, "\t");

  // 5. Remove leading/trailing empty lines
  text = text.replace(/^\s*\n+/, "").replace(/\n+\s*$/, "");

  return text;
}

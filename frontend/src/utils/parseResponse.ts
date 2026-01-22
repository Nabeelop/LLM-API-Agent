export function parseLLMResponse(text: string) {
  const match = text.match(/```python([\s\S]*?)```/);

  return {
    explanation: match
      ? text.replace(match[0], "").trim()
      : text,
    code: match ? match[1].trim() : null,
  };
}

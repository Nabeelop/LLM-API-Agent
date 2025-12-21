import { serve } from "https://deno.land/std/http/server.ts";


const html = await Deno.readTextFile("./sandbox/sandbox.html");

serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("POST only", { status: 405 });
  }

  const { code } = await req.json();

  const result = `
    <iframe id="sandbox" style="display:none"></iframe>
    <script>
      const iframe = document.getElementById("sandbox");
      iframe.srcdoc = \`${html}\`;
      iframe.onload = () => {
        iframe.contentWindow.postMessage(${JSON.stringify(code)}, "*");
        window.addEventListener("message", (e) => {
          document.body.innerText = JSON.stringify(e.data);
        });
      };
    </script>
  `;

  return new Response(result, {
    headers: { "Content-Type": "text/html" },
  });
}, { port: 8000 });

import { serve } from "https://deno.land/std/http/server.ts";
import { formatSandboxOutput } from "./formatOutput.ts";




const html = await Deno.readTextFile("./sandbox/sandbox.html");

serve(async (req) => {
  if (req.method !== "POST") {
    return new Response("POST only", { status: 405 });
  }

  const { code } = await req.json();
const result = 
JSON.stringify(code)
const cleanOutput = formatSandboxOutput(result);



;


  return new Response(cleanOutput, {
    headers: { "Content-Type": "text" },
  });
}, { port: 8000 });

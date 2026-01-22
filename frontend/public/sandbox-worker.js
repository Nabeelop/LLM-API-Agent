self.importScripts("https://cdn.jsdelivr.net/pyodide/v0.25.1/full/pyodide.js");

let pyodideReadyPromise = loadPyodide();

self.onmessage = async (event) => {
  const pyodide = await pyodideReadyPromise;

  try {
    // 🔑 STEP 1: Ensure micropip is available
    await pyodide.loadPackage("micropip");

    // 🔑 STEP 2: Install requests safely
    await pyodide.runPythonAsync(`
import micropip
await micropip.install("requests")
`);

    // 🔑 STEP 3: Run user code
    const output = await pyodide.runPythonAsync(event.data);

    self.postMessage({
      output: output ?? "✅ Code executed successfully"
    });

  } catch (err) {
    self.postMessage({ error: err.toString() });
  }
};

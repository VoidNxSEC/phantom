"""Minimal HTML playground for local API testing (GET /playground)."""

# ruff: noqa: E501 — embedded HTML/CSS/JS lines exceed ruff line length.

# Dark-theme single page: forms call same-origin API and pretty-print JSON.
PLAYGROUND_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Phantom API Playground</title>
  <style>
    :root {
      --bg: #1e1e2e; --panel: #313244; --text: #cdd6f4; --muted: #a6adc8;
      --accent: #89b4fa; --ok: #a6e3a1; --err: #f38ba8; --border: #45475a;
      --mono: ui-monospace, "Cascadia Code", Consolas, monospace;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; font-family: system-ui, sans-serif; background: var(--bg);
      color: var(--text); line-height: 1.45; padding: 1rem 1.25rem 3rem;
    }
    h1 { font-size: 1.25rem; margin: 0 0 0.5rem; color: var(--accent); }
    p.lead { color: var(--muted); margin: 0 0 1.25rem; font-size: 0.9rem; }
    section {
      background: var(--panel); border: 1px solid var(--border);
      border-radius: 8px; padding: 1rem; margin-bottom: 1rem; max-width: 52rem;
    }
    section h2 {
      margin: 0 0 0.75rem; font-size: 1rem; border-bottom: 1px solid var(--border);
      padding-bottom: 0.35rem; color: var(--accent);
    }
    label { display: block; font-size: 0.75rem; color: var(--muted); margin-top: 0.5rem; }
    input[type=text], input[type=number], textarea, select {
      width: 100%; padding: 0.45rem 0.5rem; margin-top: 0.2rem;
      border-radius: 4px; border: 1px solid var(--border); background: #181825;
      color: var(--text); font-family: var(--mono); font-size: 0.85rem;
    }
    textarea { min-height: 4rem; resize: vertical; }
    button {
      margin-top: 0.6rem; padding: 0.4rem 0.85rem; border-radius: 4px;
      border: 1px solid var(--accent); background: transparent; color: var(--accent);
      cursor: pointer; font-weight: 600; font-size: 0.85rem;
    }
    button:hover { background: rgba(137, 180, 250, 0.15); }
    button.secondary { border-color: var(--muted); color: var(--muted); }
    pre.out {
      margin: 0.75rem 0 0; padding: 0.75rem; background: #11111b; border-radius: 4px;
      overflow: auto; max-height: 18rem; font-family: var(--mono); font-size: 0.78rem;
      white-space: pre-wrap; word-break: break-word; border: 1px solid var(--border);
    }
    pre.out.ok { border-left: 3px solid var(--ok); }
    pre.out.bad { border-left: 3px solid var(--err); }
    .row { display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: flex-end; }
    .row > * { flex: 1; min-width: 8rem; }
    .hint { font-size: 0.75rem; color: var(--muted); margin-top: 0.35rem; }
  </style>
</head>
<body>
  <h1>Phantom API Playground</h1>
  <p class="lead">Calls this server’s REST API from the browser. Default origin: <code id="origin"></code></p>

  <section id="process">
    <h2>Process</h2>
    <p class="hint">POST /process — upload a UTF-8 text/markdown file for CORTEX processing.</p>
    <input type="file" id="pf"/>
    <label>chunk_size <input type="number" id="pcs" value="1024"/></label>
    <label>chunk_strategy <input type="text" id="pst" value="recursive"/></label>
    <button type="button" id="pb">Run /process</button>
    <pre class="out" id="po"></pre>
  </section>

  <section id="search">
    <h2>Search</h2>
    <p class="hint">POST /vectors/search — requires indexed vectors (use Index below first).</p>
    <label>query <input type="text" id="sq" value="What is this document about?"/></label>
    <div class="row">
      <label>top_k <input type="number" id="sk" value="5"/></label>
      <label>mode
        <select id="sm">
          <option value="dense">dense</option>
          <option value="sparse">sparse</option>
          <option value="hybrid" selected>hybrid</option>
        </select>
      </label>
    </div>
    <button type="button" id="sb">Run /vectors/search</button>
    <pre class="out" id="so"></pre>
  </section>

  <section id="index">
    <h2>Index (into vector store)</h2>
    <p class="hint">POST /vectors/index — chunk &amp; embed a text file into the in-memory FAISS store.</p>
    <input type="file" id="ifile"/>
    <button type="button" id="ib">Run /vectors/index</button>
    <pre class="out" id="io"></pre>
  </section>

  <section id="chat">
    <h2>Chat</h2>
    <p class="hint">POST /api/chat — RAG over the current vector store + LLM provider.</p>
    <label>message <input type="text" id="cm" value="Summarize the indexed context."/></label>
    <div class="row">
      <label>conversation_id <input type="text" id="cc" value="playground"/></label>
      <label>context_size <input type="number" id="cx" value="5"/></label>
      <label>llm_provider <input type="text" id="cl" value="local"/></label>
    </div>
    <button type="button" id="cb">Run /api/chat</button>
    <pre class="out" id="co"></pre>
  </section>

  <section id="models">
    <h2>Models</h2>
    <button type="button" id="mb">GET /api/models</button>
    <pre class="out" id="mo"></pre>
  </section>

  <section id="metrics">
    <h2>Metrics</h2>
    <button type="button" id="mtb">GET /api/system/metrics</button>
    <pre class="out" id="mto"></pre>
  </section>

  <section id="doctor">
    <h2>Doctor (local API)</h2>
    <p class="hint">Full stack diagnostics: run <code>phantom doctor</code> in a terminal. Here: probe this API and optionally Cortex.</p>
    <button type="button" class="secondary" id="dh">GET /health</button>
    <button type="button" class="secondary" id="dr">GET /ready</button>
    <label>Cortex base URL (may fail browser CORS)
      <input type="text" id="cxu" value="http://127.0.0.1:8087"/>
    </label>
    <button type="button" id="dc">GET Cortex /health</button>
    <pre class="out" id="do"></pre>
  </section>

  <script>
    document.getElementById("origin").textContent = location.origin;

    function fmtBody(txt) {
      try { return JSON.stringify(JSON.parse(txt), null, 2); } catch { return txt; }
    }

    async function show(el, p) {
      const pre = document.getElementById(el);
      try {
        const r = await p;
        const t = await r.text();
        pre.textContent = (r.status ? r.status + " " + r.statusText + "\\n" : "") + fmtBody(t);
        pre.className = "out " + (r.ok ? "ok" : "bad");
      } catch (e) {
        pre.textContent = String(e);
        pre.className = "out bad";
      }
    }

    document.getElementById("pb").onclick = () => {
      const f = document.getElementById("pf").files[0];
      if (!f) { alert("Choose a file"); return; }
      const fd = new FormData();
      fd.append("file", f);
      const cs = document.getElementById("pcs").value;
      const st = document.getElementById("pst").value;
      show("po", fetch("/process?chunk_size=" + encodeURIComponent(cs) + "&chunk_strategy=" + encodeURIComponent(st), {
        method: "POST", body: fd
      }));
    };

    document.getElementById("sb").onclick = () => show("so", fetch("/vectors/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: document.getElementById("sq").value,
        top_k: Number(document.getElementById("sk").value),
        mode: document.getElementById("sm").value
      })
    }));

    document.getElementById("ib").onclick = () => {
      const f = document.getElementById("ifile").files[0];
      if (!f) { alert("Choose a text file to index"); return; }
      const fd = new FormData();
      fd.append("file", f);
      show("io", fetch("/vectors/index", { method: "POST", body: fd }));
    };

    document.getElementById("cb").onclick = () => show("co", fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: document.getElementById("cm").value,
        conversation_id: document.getElementById("cc").value,
        history: [],
        context_size: Number(document.getElementById("cx").value),
        llm_provider: document.getElementById("cl").value
      })
    }));

    document.getElementById("mb").onclick = () => show("mo", fetch("/api/models"));
    document.getElementById("mtb").onclick = () => show("mto", fetch("/api/system/metrics"));
    document.getElementById("dh").onclick = () => show("do", fetch("/health"));
    document.getElementById("dr").onclick = () => show("do", fetch("/ready"));
    document.getElementById("dc").onclick = async () => {
      const base = document.getElementById("cxu").value.replace(/\\/$/, "");
      const pre = document.getElementById("do");
      try {
        const r = await fetch(base + "/health", { mode: "cors" });
        const t = await r.text();
        pre.textContent = r.status + " " + r.statusText + "\\n" + fmtBody(t);
        pre.className = "out " + (r.ok ? "ok" : "bad");
      } catch (e) {
        pre.textContent = "CORS or network error (Cortex often has no browser CORS):\\n" + e;
        pre.className = "out bad";
      }
    };
  </script>
</body>
</html>
"""

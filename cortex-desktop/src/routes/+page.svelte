<script lang="ts">
  import { onMount } from "svelte";
  import { processDocument, type ProcessDocumentResponse } from "$lib/api";

  // Types
  interface Message {
    role: "user" | "assistant";
    content: string;
    sources?: Source[];
    timestamp: number;
  }

  interface Source {
    id: number;
    text: string;
    score: number;
  }

  interface PromptTemplate {
    id: string;
    name: string;
    template: string;
    variables: string[];
    created: string;
  }

  // State
  let currentTab = $state<
    "chat" | "process" | "workbench" | "library" | "settings"
  >("chat");
  let apiUrl = $state("http://localhost:8081");
  let provider = $state("local");
  let model = $state("qwen-30b");
  let temperature = $state(0.7);
  let maxTokens = $state(2048);

  // Chat
  let messages = $state<Message[]>([]);
  let chatInput = $state("");
  let isLoading = $state(false);
  let conversationId = $state("");

  // Workbench
  let workbenchTemplate = $state("");
  let workbenchVars = $state<Record<string, string>>({});
  let workbenchResult = $state<any>(null);
  let llmResponse = $state("");

  // Library
  let savedPrompts = $state<PromptTemplate[]>([]);
  let newPromptName = $state("");

  // Status
  let apiStatus = $state<"online" | "offline" | "checking">("checking");
  let availableModels = $state<Record<string, any[]>>({});

  // File upload
  let uploadedFiles = $state<{ name: string; status: string }[]>([]);
  let isDragging = $state(false);

  // Document Processing
  let selectedFile = $state<File | null>(null);
  let chunkStrategy = $state<"recursive" | "sliding" | "simple">("recursive");
  let chunkSize = $state(1024);
  let isProcessing = $state(false);
  let processResult = $state<ProcessDocumentResponse | null>(null);
  let processError = $state("");

  // Init
  onMount(() => {
    conversationId = `conv_${Date.now()}`;
    loadFromStorage();
    checkApi();
    loadModels();
  });

  function loadFromStorage() {
    try {
      const s = localStorage.getItem("cortex_settings");
      if (s) {
        const data = JSON.parse(s);
        apiUrl = data.apiUrl || apiUrl;
        provider = data.provider || provider;
        model = data.model || model;
        temperature = data.temperature ?? temperature;
        maxTokens = data.maxTokens || maxTokens;
      }
      const p = localStorage.getItem("cortex_prompts");
      if (p) savedPrompts = JSON.parse(p);
    } catch {}
  }

  function saveSettings() {
    localStorage.setItem(
      "cortex_settings",
      JSON.stringify({ apiUrl, provider, model, temperature, maxTokens }),
    );
  }

  function savePrompts() {
    localStorage.setItem("cortex_prompts", JSON.stringify(savedPrompts));
  }

  async function checkApi() {
    apiStatus = "checking";
    try {
      const res = await fetch(`${apiUrl}/health`);
      apiStatus = res.ok ? "online" : "offline";
    } catch {
      apiStatus = "offline";
    }
  }

  async function loadModels() {
    try {
      const res = await fetch(`${apiUrl}/api/models`);
      if (res.ok) availableModels = await res.json();
    } catch {}
  }

  // Chat
  async function sendMessage() {
    if (!chatInput.trim() || isLoading) return;

    messages = [
      ...messages,
      { role: "user", content: chatInput.trim(), timestamp: Date.now() },
    ];
    const question = chatInput;
    chatInput = "";
    isLoading = true;

    try {
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: question,
          conversation_id: conversationId,
          history: messages
            .slice(-10)
            .map((m) => ({ role: m.role, content: m.content })),
          context_size: 5,
          llm_provider: provider,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        messages = [
          ...messages,
          {
            role: "assistant",
            content: data.message.content,
            sources: data.message.sources,
            timestamp: Date.now(),
          },
        ];
      } else {
        messages = [
          ...messages,
          { role: "assistant", content: "❌ API Error", timestamp: Date.now() },
        ];
      }
    } catch {
      messages = [
        ...messages,
        {
          role: "assistant",
          content: "❌ Connection failed",
          timestamp: Date.now(),
        },
      ];
    }
    isLoading = false;
  }

  function clearChat() {
    messages = [];
    conversationId = `conv_${Date.now()}`;
  }

  // Workbench
  function extractVars(t: string): string[] {
    const m = t.match(/\{(\w+)\}/g) || [];
    return [...new Set(m.map((x) => x.slice(1, -1)))];
  }

  $effect(() => {
    const vars = extractVars(workbenchTemplate);
    const newVars: Record<string, string> = {};
    vars.forEach((v) => (newVars[v] = workbenchVars[v] || ""));
    workbenchVars = newVars;
  });

  async function testPrompt() {
    try {
      const res = await fetch(`${apiUrl}/api/prompt/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          template: workbenchTemplate,
          variables: workbenchVars,
        }),
      });
      if (res.ok) workbenchResult = await res.json();
    } catch {}
  }

  async function runWithLLM() {
    if (!workbenchResult?.rendered) return;
    isLoading = true;
    try {
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: workbenchResult.rendered,
          conversation_id: "workbench",
          history: [],
          context_size: 0,
          llm_provider: provider,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        llmResponse = data.message.content;
      }
    } catch {}
    isLoading = false;
  }

  // Library
  function saveCurrentPrompt() {
    if (!newPromptName.trim() || !workbenchTemplate.trim()) return;
    savedPrompts = [
      {
        id: `p_${Date.now()}`,
        name: newPromptName,
        template: workbenchTemplate,
        variables: extractVars(workbenchTemplate),
        created: new Date().toISOString(),
      },
      ...savedPrompts,
    ];
    savePrompts();
    newPromptName = "";
  }

  function loadPrompt(p: PromptTemplate) {
    workbenchTemplate = p.template;
    currentTab = "workbench";
  }

  function deletePrompt(id: string) {
    savedPrompts = savedPrompts.filter((p) => p.id !== id);
    savePrompts();
  }

  // File upload
  async function handleDrop(e: DragEvent) {
    e.preventDefault();
    isDragging = false;
    const files = Array.from(e.dataTransfer?.files || []);
    if (!files.length) return;

    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));

    uploadedFiles = [
      ...uploadedFiles,
      ...files.map((f) => ({ name: f.name, status: "uploading" })),
    ];

    try {
      const res = await fetch(`${apiUrl}/api/upload`, {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        uploadedFiles = uploadedFiles.map((f) => {
          const r = data.files?.find((x: any) => x.filename === f.name);
          return r ? { ...f, status: r.status } : f;
        });
      }
    } catch {
      uploadedFiles = uploadedFiles.map((f) =>
        f.status === "uploading" ? { ...f, status: "error" } : f,
      );
    }
  }

  // Document Processing
  function handleFileSelect(e: Event) {
    const input = e.target as HTMLInputElement;
    if (input.files?.[0]) {
      selectedFile = input.files[0];
      processResult = null;
      processError = "";
    }
  }

  async function handleProcess() {
    if (!selectedFile) {
      processError = "Please select a file first";
      return;
    }

    isProcessing = true;
    processError = "";
    processResult = null;

    try {
      const response = await processDocument({
        file: selectedFile,
        chunkStrategy,
        chunkSize,
      });
      processResult = response;
    } catch (e: any) {
      processError = e.message || "Processing failed";
    } finally {
      isProcessing = false;
    }
  }

  // Helper for nav button classes
  function navClass(tab: string): string {
    const base =
      "w-10 h-10 rounded flex items-center justify-center transition-all border";
    return currentTab === tab
      ? `${base} border-[#f5c2e7] bg-[#f5c2e7]/10 text-[#f5c2e7]`
      : `${base} border-transparent text-[#585b70] hover:border-[#313244] hover:bg-[#313244]/50`;
  }
</script>

<div
  class="h-screen flex bg-[#11111b] text-[#cdd6f4] overflow-hidden font-mono"
>
  <!-- Sidebar -->
  <nav
    class="w-16 bg-[#181825] border-r border-[#313244] flex flex-col items-center py-4 gap-1"
  >
    <div
      class="w-10 h-10 rounded bg-[#cba6f7] flex items-center justify-center mb-4 border border-[#cba6f7]/30"
    >
      <span class="text-sm font-bold text-[#11111b]">C</span>
    </div>

    <button
      onclick={() => (currentTab = "chat")}
      class={navClass("chat")}
      title="Chat"
    >
      <svg
        class="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
        ></path>
      </svg>
    </button>

    <button
      onclick={() => (currentTab = "process")}
      class={navClass("process")}
      title="Document Processing"
    >
      <svg
        class="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        ></path>
      </svg>
    </button>

    <button
      onclick={() => (currentTab = "workbench")}
      class={navClass("workbench")}
      title="Prompt Workbench"
    >
      <svg
        class="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
        ></path>
      </svg>
    </button>

    <button
      onclick={() => (currentTab = "library")}
      class={navClass("library")}
      title="Library"
    >
      <svg
        class="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
        ></path>
      </svg>
    </button>

    <button
      onclick={() => (currentTab = "settings")}
      class={navClass("settings")}
      title="Settings"
    >
      <svg
        class="w-6 h-6"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
        ></path>
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
        ></path>
      </svg>
    </button>

    <div class="flex-1"></div>
    <div
      class="w-2 h-2 rounded-full {apiStatus === 'online'
        ? 'bg-[#a6e3a1]'
        : apiStatus === 'offline'
          ? 'bg-[#f38ba8]'
          : 'bg-[#f9e2af] animate-pulse'}"
      title="API: {apiStatus}"
    ></div>
  </nav>

  <!-- Main -->
  <main class="flex-1 flex flex-col overflow-hidden">
    <!-- CHAT TAB -->
    {#if currentTab === "chat"}
      <div class="flex-1 flex flex-col p-6 overflow-hidden">
        <header class="flex items-center justify-between mb-6">
          <div>
            <h1 class="text-2xl font-bold">Chat</h1>
            <p class="text-gray-500 text-sm">RAG-powered conversation</p>
          </div>
          <button
            onclick={clearChat}
            class="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm"
            >Clear</button
          >
        </header>

        <div class="flex-1 overflow-y-auto space-y-4 pr-4">
          {#if messages.length === 0}
            <div class="h-full flex items-center justify-center text-gray-600">
              <div class="text-center">
                <p class="text-lg">Start a conversation</p>
                <p class="text-sm mt-1">Ask anything from the knowledge base</p>
              </div>
            </div>
          {/if}

          {#each messages as msg (msg.timestamp)}
            <div
              class="flex {msg.role === 'user'
                ? 'justify-end'
                : 'justify-start'}"
            >
              <div
                class="max-w-2xl rounded-2xl px-5 py-3 shadow-lg {msg.role ===
                'user'
                  ? 'bg-gradient-to-r from-cyan-600 to-blue-600'
                  : 'bg-gray-800'}"
              >
                <p class="whitespace-pre-wrap">{msg.content}</p>
                {#if msg.sources?.length}
                  <details class="mt-3 text-xs text-gray-400">
                    <summary class="cursor-pointer"
                      >📚 {msg.sources.length} sources</summary
                    >
                    <ul class="mt-2 space-y-1">
                      {#each msg.sources as src}
                        <li class="pl-2 border-l-2 border-cyan-500">
                          {src.text}
                        </li>
                      {/each}
                    </ul>
                  </details>
                {/if}
              </div>
            </div>
          {/each}

          {#if isLoading}
            <div class="flex">
              <div class="bg-gray-800 rounded-2xl px-5 py-3 flex gap-1">
                <span class="w-2 h-2 bg-cyan-500 rounded-full animate-bounce"
                ></span>
                <span
                  class="w-2 h-2 bg-cyan-500 rounded-full animate-bounce"
                  style="animation-delay: 0.1s"
                ></span>
                <span
                  class="w-2 h-2 bg-cyan-500 rounded-full animate-bounce"
                  style="animation-delay: 0.2s"
                ></span>
              </div>
            </div>
          {/if}
        </div>

        <div class="mt-4 flex gap-3">
          <input
            type="text"
            bind:value={chatInput}
            onkeydown={(e) => e.key === "Enter" && sendMessage()}
            placeholder="Ask anything..."
            class="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-5 py-3 focus:outline-none focus:border-cyan-500"
          />
          <button
            onclick={sendMessage}
            disabled={isLoading || !chatInput.trim()}
            class="px-6 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-xl font-medium disabled:opacity-50"
            >Send</button
          >
        </div>
      </div>
    {/if}

    <!-- PROCESS TAB -->
    {#if currentTab === "process"}
      <div class="flex-1 flex flex-col p-6 overflow-hidden gap-4">
        <header>
          <h1 class="text-xl font-mono font-bold text-[#cba6f7]">
            Document Processing
          </h1>
          <p class="text-xs text-[#585b70] mt-1">CORTEX extraction pipeline</p>
        </header>

        <div class="flex-1 flex flex-col overflow-hidden gap-4">
          <!-- Upload Section -->
          <div
            class="bg-[#1e1e2e] border border-[#313244] rounded p-4 space-y-3"
          >
            <div>
              <label
                for="file-input"
                class="block text-xs font-mono text-[#585b70] mb-2 uppercase"
              >
                Document
              </label>
              <input
                id="file-input"
                type="file"
                accept=".md,.txt"
                onchange={handleFileSelect}
                class="block w-full text-sm text-[#cdd6f4] file:mr-3 file:py-2 file:px-4 file:rounded file:border file:border-[#f5c2e7] file:text-xs file:font-mono file:bg-transparent file:text-[#f5c2e7] hover:file:bg-[#f5c2e7]/10 bg-[#181825] rounded border border-[#313244] cursor-pointer"
              />
              {#if selectedFile}
                <p class="mt-2 text-xs text-[#a6adc8] font-mono">
                  → {selectedFile.name}
                </p>
              {/if}
            </div>

            <div class="grid grid-cols-2 gap-3">
              <div>
                <label
                  for="chunk-strategy"
                  class="block text-xs font-mono text-[#585b70] mb-2 uppercase"
                >
                  Strategy
                </label>
                <select
                  id="chunk-strategy"
                  bind:value={chunkStrategy}
                  class="w-full bg-[#181825] border border-[#313244] rounded px-3 py-2 text-sm font-mono text-[#cdd6f4] focus:outline-none focus:border-[#cba6f7]"
                >
                  <option value="recursive">recursive</option>
                  <option value="sliding">sliding</option>
                  <option value="simple">simple</option>
                </select>
              </div>

              <div>
                <label
                  for="chunk-size"
                  class="block text-xs font-mono text-[#585b70] mb-2 uppercase"
                >
                  Tokens
                </label>
                <input
                  id="chunk-size"
                  type="number"
                  min="256"
                  max="2048"
                  step="128"
                  bind:value={chunkSize}
                  class="w-full bg-[#181825] border border-[#313244] rounded px-3 py-2 text-sm font-mono text-[#cdd6f4] focus:outline-none focus:border-[#cba6f7]"
                />
              </div>
            </div>

            <button
              onclick={handleProcess}
              disabled={!selectedFile || isProcessing}
              class="w-full py-2 border border-[#f5c2e7] bg-transparent text-[#f5c2e7] hover:bg-[#f5c2e7]/10 rounded font-mono text-sm disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              {isProcessing ? "processing..." : "execute"}
            </button>
          </div>

          <!-- Results Section -->
          {#if processError}
            <div class="p-3 bg-[#1e1e2e] border border-[#f38ba8] rounded">
              <p class="text-[#f38ba8] text-sm font-mono">✗ {processError}</p>
            </div>
          {/if}

          {#if processResult}
            <div
              class="flex-1 overflow-auto bg-[#1e1e2e] border border-[#313244] rounded p-4 space-y-3"
            >
              <div
                class="flex justify-between items-start border-b border-[#313244] pb-2"
              >
                <div>
                  <h2 class="text-sm font-mono font-bold text-[#cba6f7]">
                    results
                  </h2>
                  <span class="text-xs text-[#585b70] font-mono"
                    >{processResult.filename}</span
                  >
                </div>
                <span class="text-xs text-[#a6adc8] font-mono">
                  {processResult.processing_time.toFixed(2)}s
                </span>
              </div>

              {#if processResult.insights?.themes}
                <div class="space-y-2">
                  {#each processResult.insights.themes as theme, i}
                    <div
                      class="bg-[#181825] border-l-2 border-[#f5c2e7] p-3 rounded-r"
                    >
                      <div class="flex justify-between items-start">
                        <h4 class="font-mono text-sm text-[#cdd6f4]">
                          {theme.title}
                        </h4>
                        <span
                          class="px-2 py-0.5 text-xs font-mono rounded border {theme.confidence ===
                          'high'
                            ? 'border-[#a6e3a1] text-[#a6e3a1]'
                            : theme.confidence === 'medium'
                              ? 'border-[#f9e2af] text-[#f9e2af]'
                              : 'border-[#585b70] text-[#585b70]'}"
                        >
                          {theme.confidence}
                        </span>
                      </div>
                      <p class="mt-2 text-xs text-[#a6adc8]">
                        {theme.description}
                      </p>
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          {/if}

          {#if isProcessing}
            <div class="flex items-center justify-center p-8">
              <span class="text-[#cba6f7] font-mono text-sm animate-pulse"
                >processing...</span
              >
            </div>
          {/if}
        </div>
      </div>
    {/if}

    <!-- WORKBENCH TAB -->
    {#if currentTab === "workbench"}
      <div class="flex-1 flex overflow-hidden">
        <div class="flex-1 flex flex-col p-6 border-r border-gray-800">
          <header class="flex items-center justify-between mb-4">
            <div>
              <h1 class="text-2xl font-bold">Prompt Workbench</h1>
              <p class="text-gray-500 text-sm">Create and test prompts</p>
            </div>
            <div class="flex gap-2">
              <button
                onclick={testPrompt}
                class="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm"
                >Test</button
              >
              <button
                onclick={runWithLLM}
                disabled={!workbenchResult?.rendered || isLoading}
                class="px-4 py-2 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg text-sm disabled:opacity-50"
                >Run LLM</button
              >
            </div>
          </header>

          <div class="flex-1 flex flex-col gap-4 overflow-hidden">
            <div class="flex-1">
              <label
                for="workbench-template"
                class="block text-sm text-gray-400 mb-2"
                >Template (use {"{variable}"} syntax)</label
              >
              <textarea
                id="workbench-template"
                bind:value={workbenchTemplate}
                placeholder="Context: {'{context}'}&#10;&#10;Question: {'{question}'}&#10;&#10;Answer:"
                class="w-full h-full bg-gray-900 border border-gray-800 rounded-xl px-4 py-3 font-mono text-sm resize-none focus:outline-none focus:border-cyan-500"
              ></textarea>
            </div>

            {#if Object.keys(workbenchVars).length > 0}
              <div class="space-y-2">
                <span class="block text-sm text-gray-400">Variables</span>
                {#each Object.entries(workbenchVars) as [key, _]}
                  <div class="flex gap-2 items-center">
                    <span class="w-28 text-sm text-cyan-400 font-mono"
                      >{"{" + key + "}"}</span
                    >
                    <input
                      type="text"
                      bind:value={workbenchVars[key]}
                      class="flex-1 bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
                      placeholder="Value for {key}"
                    />
                  </div>
                {/each}
              </div>
            {/if}

            <div class="flex gap-2">
              <input
                type="text"
                bind:value={newPromptName}
                placeholder="Prompt name..."
                class="flex-1 bg-gray-900 border border-gray-800 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-cyan-500"
              />
              <button
                onclick={saveCurrentPrompt}
                disabled={!newPromptName.trim() || !workbenchTemplate.trim()}
                class="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm disabled:opacity-50"
                >Save</button
              >
            </div>
          </div>
        </div>

        <div class="w-96 flex flex-col p-6 overflow-hidden">
          <h2 class="text-lg font-semibold mb-4">Output</h2>

          {#if workbenchResult}
            <div class="mb-4 p-3 bg-gray-800 rounded-lg">
              <div class="flex justify-between text-sm">
                <span class="text-gray-400">Tokens:</span>
                <span class="text-cyan-400 font-mono"
                  >{workbenchResult.tokens}</span
                >
              </div>
              <div class="flex justify-between text-sm mt-1">
                <span class="text-gray-400">Status:</span>
                <span
                  class={workbenchResult.success
                    ? "text-green-400"
                    : "text-red-400"}
                  >{workbenchResult.success ? "✓ Valid" : "✗ Error"}</span
                >
              </div>
            </div>

            <div class="flex-1 overflow-auto space-y-4">
              <div>
                <span class="block text-sm text-gray-400 mb-2">Rendered</span>
                <pre
                  class="bg-gray-900 rounded-xl p-4 text-sm font-mono whitespace-pre-wrap overflow-auto max-h-40">{workbenchResult.rendered}</pre>
              </div>

              {#if llmResponse}
                <div>
                  <span class="block text-sm text-gray-400 mb-2"
                    >LLM Response</span
                  >
                  <div
                    class="bg-gray-900 rounded-xl p-4 text-sm whitespace-pre-wrap"
                  >
                    {llmResponse}
                  </div>
                </div>
              {/if}
            </div>
          {:else}
            <div class="flex-1 flex items-center justify-center text-gray-600">
              <p>Click "Test" to preview</p>
            </div>
          {/if}
        </div>
      </div>
    {/if}

    <!-- LIBRARY TAB -->
    {#if currentTab === "library"}
      <div class="flex-1 p-6 overflow-auto">
        <header class="mb-6">
          <h1 class="text-2xl font-bold">Prompt Library</h1>
          <p class="text-gray-500 text-sm">
            {savedPrompts.length} saved prompts
          </p>
        </header>

        {#if savedPrompts.length === 0}
          <div class="text-center text-gray-600 py-20">
            <p class="text-lg">No saved prompts</p>
            <p class="text-sm mt-1">Create and save prompts in the Workbench</p>
          </div>
        {:else}
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {#each savedPrompts as prompt (prompt.id)}
              <div
                class="bg-gray-800/50 backdrop-blur border border-gray-700 rounded-xl p-5 hover:border-cyan-500/50 transition-colors"
              >
                <div class="flex justify-between items-start mb-3">
                  <h3 class="font-semibold">{prompt.name}</h3>
                  <button
                    onclick={() => deletePrompt(prompt.id)}
                    class="text-gray-500 hover:text-red-400">✕</button
                  >
                </div>

                <pre
                  class="text-xs text-gray-400 bg-gray-900/50 rounded-lg p-3 mb-3 max-h-24 overflow-hidden font-mono">{prompt.template.slice(
                    0,
                    100,
                  )}{prompt.template.length > 100 ? "..." : ""}</pre>

                <div class="flex justify-between items-center">
                  <div class="flex gap-1">
                    {#each prompt.variables.slice(0, 2) as v}
                      <span
                        class="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 rounded text-xs font-mono"
                        >{v}</span
                      >
                    {/each}
                    {#if prompt.variables.length > 2}
                      <span class="text-xs text-gray-500"
                        >+{prompt.variables.length - 2}</span
                      >
                    {/if}
                  </div>
                  <button
                    onclick={() => loadPrompt(prompt)}
                    class="text-sm text-cyan-400 hover:text-cyan-300"
                    >Load →</button
                  >
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <!-- SETTINGS TAB -->
    {#if currentTab === "settings"}
      <div class="flex-1 p-6 overflow-auto">
        <header class="mb-6">
          <h1 class="text-2xl font-bold">Settings</h1>
          <p class="text-gray-500 text-sm">Configure CORTEX</p>
        </header>

        <div class="max-w-xl space-y-6">
          <div>
            <label
              for="api-url"
              class="block text-sm font-medium text-gray-400 mb-2"
              >API URL</label
            >
            <input
              id="api-url"
              type="text"
              bind:value={apiUrl}
              onchange={saveSettings}
              class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label
              for="provider"
              class="block text-sm font-medium text-gray-400 mb-2"
              >Provider</label
            >
            <select
              id="provider"
              bind:value={provider}
              onchange={saveSettings}
              class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 focus:outline-none focus:border-cyan-500"
            >
              <option value="local">Local (LLaMa)</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
            </select>
          </div>

          <div>
            <label
              for="model"
              class="block text-sm font-medium text-gray-400 mb-2">Model</label
            >
            <select
              id="model"
              bind:value={model}
              onchange={saveSettings}
              class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 focus:outline-none focus:border-cyan-500"
            >
              {#if availableModels[provider]}
                {#each availableModels[provider] as m}
                  <option value={m.id}>{m.name}</option>
                {/each}
              {:else}
                <option value="default">Default</option>
              {/if}
            </select>
          </div>

          <div>
            <label
              for="temperature"
              class="block text-sm font-medium text-gray-400 mb-2"
              >Temperature: <span class="text-cyan-400"
                >{temperature.toFixed(1)}</span
              ></label
            >
            <input
              id="temperature"
              type="range"
              min="0"
              max="2"
              step="0.1"
              bind:value={temperature}
              onchange={saveSettings}
              class="w-full accent-cyan-500"
            />
          </div>

          <div>
            <label
              for="max-tokens"
              class="block text-sm font-medium text-gray-400 mb-2"
              >Max Tokens</label
            >
            <input
              id="max-tokens"
              type="number"
              bind:value={maxTokens}
              onchange={saveSettings}
              class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <span class="block text-sm font-medium text-gray-400 mb-2"
              >Upload Documents</span
            >
            <div
              role="region"
              aria-label="File upload drop zone"
              ondrop={handleDrop}
              ondragover={(e) => {
                e.preventDefault();
                isDragging = true;
              }}
              ondragleave={() => (isDragging = false)}
              class="border-2 border-dashed rounded-xl p-8 text-center transition-colors {isDragging
                ? 'border-cyan-500 bg-cyan-500/10'
                : 'border-gray-700'}"
            >
              <p class="text-gray-500">Drop files (PDF, MD, TXT)</p>
            </div>
            {#if uploadedFiles.length > 0}
              <ul class="mt-3 space-y-1 text-sm">
                {#each uploadedFiles as f}
                  <li class="flex justify-between">
                    <span>{f.name}</span>
                    <span
                      class={f.status === "queued"
                        ? "text-green-400"
                        : f.status === "uploading"
                          ? "text-yellow-400"
                          : "text-red-400"}>{f.status}</span
                    >
                  </li>
                {/each}
              </ul>
            {/if}
          </div>

          <button
            onclick={() => {
              saveSettings();
              checkApi();
            }}
            class="w-full py-3 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-xl font-medium hover:from-cyan-500 hover:to-blue-500"
            >Save & Reconnect</button
          >
        </div>
      </div>
    {/if}
  </main>
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: "Inter", system-ui, sans-serif;
  }
</style>

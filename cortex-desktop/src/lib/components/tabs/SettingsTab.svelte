<script lang="ts">
  import { appState } from "$lib/state.svelte";
</script>

<div class="flex-1 p-8 overflow-auto bg-[#0A0A0A] relative">
  <div class="absolute top-0 left-0 w-96 h-96 bg-blue-500/5 rounded-full blur-[120px] pointer-events-none"></div>

  <header class="mb-10 z-10 shrink-0">
    <h1 class="text-3xl font-light text-white tracking-tight">Settings</h1>
    <p class="text-zinc-500 text-sm mt-1">Configure CORTEX infrastructure and LLM providers</p>
  </header>

  <div class="grid grid-cols-1 lg:grid-cols-2 gap-8 z-10 relative max-w-6xl">
    <!-- Provider & API Settings -->
    <div class="space-y-6">
      <div class="bg-zinc-900/50 border border-zinc-800/80 rounded-2xl p-6 backdrop-blur-md">
        <h2 class="text-base font-medium text-zinc-200 mb-6 flex items-center gap-2">
          <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
          Connectivity
        </h2>

        <div class="space-y-5">
          <div>
            <label class="block text-xs font-semibold text-zinc-500 mb-2 uppercase tracking-wider">Cortex API Endpoint</label>
            <div class="relative">
              <input
                type="text"
                value={appState.apiUrl}
                disabled
                class="w-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-500 focus:outline-none transition-all font-mono cursor-not-allowed"
                title="Auto-detected from window origin. Backend is proxied via Vite in dev."
              />
              <div class="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2 px-2 py-1 rounded-md bg-zinc-900 border border-zinc-800">
                <span class="w-1.5 h-1.5 rounded-full {appState.apiStatus === 'online' ? 'bg-emerald-400' : 'bg-rose-500'}"></span>
                <span class="text-[10px] uppercase font-bold text-zinc-400 tracking-wider w-12 text-center">
                  {appState.apiStatus}
                </span>
              </div>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-semibold text-zinc-500 mb-2 uppercase tracking-wider">Inference Provider</label>
              <select
                bind:value={appState.provider}
                onchange={() => appState.saveSettings()}
                class="w-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all cursor-pointer appearance-none"
              >
                <option value="tensor_forge">Local Tensor Engine</option>
                <option value="openai">OpenAI Managed</option>
                <option value="anthropic">Anthropic API</option>
              </select>
            </div>

            <div>
              <label class="block text-xs font-semibold text-zinc-500 mb-2 uppercase tracking-wider">Model Selection</label>
              <select
                bind:value={appState.model}
                onchange={() => appState.saveSettings()}
                class="w-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all cursor-pointer appearance-none"
              >
                {#if appState.availableModels[appState.provider]}
                  {#each appState.availableModels[appState.provider] as m}
                    <option value={m.id}>{m.name}</option>
                  {/each}
                {:else}
                  <option value="default">Default Active Model</option>
                {/if}
              </select>
            </div>
          </div>
        </div>
      </div>

      <div class="bg-zinc-900/50 border border-zinc-800/80 rounded-2xl p-6 backdrop-blur-md">
        <h2 class="text-base font-medium text-zinc-200 mb-6 flex items-center gap-2">
          <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path></svg>
          Generation Parameters
        </h2>

        <div class="space-y-6">
          <div>
            <div class="flex justify-between items-center mb-2">
              <label class="block text-xs font-semibold text-zinc-500 uppercase tracking-wider">Temperature</label>
              <span class="text-blue-400 font-mono text-sm px-2 py-0.5 bg-blue-500/10 rounded">{appState.temperature.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0" max="2" step="0.05"
              bind:value={appState.temperature}
              onchange={() => appState.saveSettings()}
              class="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-blue-500"
            />
            <div class="flex justify-between mt-1 text-[10px] text-zinc-600 uppercase font-semibold">
              <span>Deterministic</span>
              <span>Creative</span>
            </div>
          </div>

          <div>
            <label class="block text-xs font-semibold text-zinc-500 mb-2 uppercase tracking-wider">Context Length (Tokens)</label>
            <input
              type="number"
              bind:value={appState.maxTokens}
              onchange={() => appState.saveSettings()}
              class="w-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-3 text-sm text-zinc-200 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all font-mono"
            />
          </div>
        </div>
      </div>
      
      <button
        onclick={() => {
          appState.saveSettings();
          appState.checkApi();
        }}
        class="w-full py-4 bg-zinc-100 hover:bg-white text-zinc-900 rounded-xl font-medium transition-all shadow-[0_0_15px_rgba(255,255,255,0.05)] flex items-center justify-center gap-2"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>
        Save Configuration & Reconnect
      </button>
    </div>

    <!-- Data Ingestion Area -->
    <div class="bg-zinc-900/50 border border-zinc-800/80 rounded-2xl p-6 backdrop-blur-md h-full flex flex-col">
      <h2 class="text-base font-medium text-zinc-200 mb-6 flex items-center gap-2 shrink-0">
        <svg class="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path></svg>
        Direct Ingestion (Raw Data)
      </h2>

      <div
        role="region"
        ondrop={(e) => appState.handleDrop(e)}
        ondragover={(e) => { e.preventDefault(); appState.isDragging = true; }}
        ondragleave={() => (appState.isDragging = false)}
        class="flex-1 min-h-[200px] border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-8 transition-all group overflow-hidden relative
          {appState.isDragging ? 'border-blue-500 bg-blue-500/5' : 'border-zinc-800 bg-zinc-900/30 hover:bg-zinc-900/80 hover:border-zinc-700'}"
      >
        <div class="absolute inset-0 bg-blue-500/20 translate-y-full group-hover:translate-y-0 transition-transform duration-700 ease-out opacity-0 group-hover:opacity-100 pointer-events-none blur-3xl"></div>
        <div class="w-16 h-16 bg-zinc-800 rounded-2xl flex items-center justify-center mb-6 shadow-sm border border-zinc-700 group-hover:-translate-y-2 transition-transform duration-500">
          <svg class="w-8 h-8 text-zinc-500 group-hover:text-blue-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
        </div>
        <p class="text-zinc-300 font-medium mb-1 relative z-10">Drop files to ingest</p>
        <p class="text-zinc-500 text-sm relative z-10">Supported: PDF, Markdown, Text, CSV</p>
      </div>

      {#if appState.uploadedFiles.length > 0}
        <div class="mt-6 space-y-2 shrink-0 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
          <span class="block text-xs font-semibold text-zinc-500 mb-3 uppercase tracking-wider">Ingestion Queue</span>
          {#each appState.uploadedFiles as f}
            <div class="flex items-center justify-between p-3 bg-zinc-950/50 border border-zinc-800/80 rounded-xl">
              <span class="text-sm text-zinc-300 truncate pr-4 flex-1">{f.name}</span>
              <span class="flex items-center gap-2">
                {#if f.status === 'queued'}
                  <span class="w-2 h-2 rounded-full bg-blue-400"></span><span class="text-xs text-blue-400 uppercase font-semibold">Queued</span>
                {:else if f.status === 'uploading'}
                  <span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span><span class="text-xs text-amber-400 uppercase font-semibold">Processing</span>
                {:else if f.status === 'error'}
                  <span class="w-2 h-2 rounded-full bg-rose-500"></span><span class="text-xs text-rose-500 uppercase font-semibold">Failed</span>
                {:else}
                  <span class="w-2 h-2 rounded-full bg-emerald-400"></span><span class="text-xs text-emerald-400 uppercase font-semibold">Ingested</span>
                {/if}
              </span>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  </div>
</div>

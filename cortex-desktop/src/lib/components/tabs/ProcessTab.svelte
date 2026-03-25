<script lang="ts">
  import { appState } from "$lib/state.svelte";
</script>

<div class="flex-1 flex flex-col p-8 overflow-hidden bg-[#0A0A0A] relative">
  <div class="absolute top-0 right-0 w-96 h-96 bg-purple-500/5 rounded-full blur-[120px] pointer-events-none"></div>

  <header class="mb-8 z-10">
    <h1 class="text-3xl font-light text-white tracking-tight">Data Processing</h1>
    <p class="text-zinc-500 text-sm mt-1">CORTEX extraction & ingestion pipeline</p>
  </header>

  <div class="flex-1 overflow-y-auto pr-2 pb-4 z-10 space-y-6">
    <!-- Config Card -->
    <div class="bg-zinc-900/50 border border-zinc-800/80 rounded-2xl p-6 backdrop-blur-md">
      <h2 class="text-lg font-medium text-zinc-200 mb-6 flex items-center gap-2">
        <svg class="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
        Pipeline Configuration
      </h2>

      <div class="space-y-5">
        <div>
          <label class="block text-xs font-semibold text-zinc-500 mb-2 uppercase tracking-wider">Target Document</label>
          <div class="relative group">
            <input
              type="file"
              accept=".md,.txt,.pdf"
              onchange={(e) => {
                const target = e.target as HTMLInputElement;
                if (target.files?.[0]) {
                  appState.selectedFile = target.files[0];
                  appState.processError = "";
                  appState.processResult = null;
                }
              }}
              class="block w-full text-sm text-zinc-400 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-zinc-800 file:text-zinc-200 hover:file:bg-zinc-700 bg-zinc-950/50 rounded-xl border border-zinc-800 cursor-pointer focus:outline-none focus:border-purple-500/50 transition-colors"
            />
          </div>
          {#if appState.selectedFile}
            <p class="mt-2 text-sm text-cyan-400 font-mono">↳ {appState.selectedFile.name}</p>
          {/if}
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-xs font-semibold text-zinc-500 mb-2 uppercase tracking-wider">Strategy</label>
            <select
              bind:value={appState.chunkStrategy}
              class="w-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-2.5 text-sm text-zinc-300 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all cursor-pointer appearance-none"
            >
              <option value="recursive">Recursive Chunking</option>
              <option value="sliding">Sliding Window</option>
              <option value="simple">Simple Split</option>
            </select>
          </div>

          <div>
            <label class="block text-xs font-semibold text-zinc-500 mb-2 uppercase tracking-wider">Max Tokens</label>
            <input
              type="number"
              min="256" max="2048" step="128"
              bind:value={appState.chunkSize}
              class="w-full bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-2.5 text-sm text-zinc-300 focus:outline-none focus:border-purple-500/50 focus:ring-1 focus:ring-purple-500/50 transition-all"
            />
          </div>
        </div>

        <button
          onclick={() => appState.handleProcess()}
          disabled={!appState.selectedFile || appState.isProcessing}
          class="w-full py-3 bg-zinc-100 hover:bg-white text-zinc-900 rounded-xl font-medium transition-all shadow-[0_0_15px_rgba(255,255,255,0.1)] disabled:opacity-50 disabled:shadow-none flex items-center justify-center gap-2 mt-2"
        >
          {#if appState.isProcessing}
            <span class="w-4 h-4 rounded-full border-2 border-zinc-900 border-t-transparent animate-spin"></span>
            Processing...
          {:else}
            Execute Pipeline
          {/if}
        </button>
      </div>
    </div>

    <!-- Error state -->
    {#if appState.processError}
      <div class="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-start gap-3">
        <svg class="w-5 h-5 text-rose-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
        <p class="text-rose-400 text-sm leading-relaxed">{appState.processError}</p>
      </div>
    {/if}

    <!-- Result state -->
    {#if appState.processResult}
      <div class="bg-zinc-900/50 border border-zinc-800/80 rounded-2xl p-6 backdrop-blur-md animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div class="flex justify-between items-start border-b border-zinc-800/80 pb-4 mb-4">
          <div>
            <h2 class="text-lg font-medium text-zinc-200">Extraction Results</h2>
            <span class="text-xs text-zinc-500 font-mono mt-1 block">{appState.processResult.filename}</span>
          </div>
          <div class="text-right">
            <span class="text-sm font-medium text-zinc-300">{appState.processResult.processing_time.toFixed(2)}s</span>
            <span class="text-[10px] text-zinc-500 block uppercase tracking-wide">Duration</span>
          </div>
        </div>

        {#if appState.processResult.insights?.themes}
          <div class="space-y-3 mt-4">
            {#each appState.processResult.insights.themes as theme}
              <div class="bg-zinc-950/50 border border-zinc-800/50 p-4 rounded-xl hover:border-zinc-700/50 transition-colors">
                <div class="flex justify-between items-start mb-2">
                  <h4 class="font-medium text-zinc-200">{theme.title}</h4>
                  <span class="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider rounded-md border 
                    {theme.confidence === 'high' ? 'border-green-500/30 text-green-400 bg-green-500/10' : 
                     theme.confidence === 'medium' ? 'border-amber-500/30 text-amber-400 bg-amber-500/10' : 
                     'border-zinc-500/30 text-zinc-400 bg-zinc-500/10'}">
                    {theme.confidence}
                  </span>
                </div>
                <p class="text-sm text-zinc-400 leading-relaxed">{theme.description}</p>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

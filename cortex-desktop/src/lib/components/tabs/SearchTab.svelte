<script lang="ts">
  import { appState } from "$lib/state.svelte";
</script>

<div class="flex-1 flex flex-col p-8 overflow-hidden bg-[#0A0A0A] relative">
  <div class="absolute top-0 left-0 w-96 h-96 bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none"></div>

  <header class="mb-8 z-10 shrink-0">
    <h1 class="text-3xl font-light text-white tracking-tight">Vector Search</h1>
    <p class="text-zinc-500 text-sm mt-1">High-performance semantic retrieval</p>
  </header>

  <div class="flex-1 flex flex-col overflow-hidden gap-6 z-10">
    <!-- Search Box -->
    <div class="bg-zinc-900/50 border border-zinc-800/80 rounded-2xl p-6 backdrop-blur-md shrink-0">
      <label class="block text-xs font-semibold text-zinc-500 mb-3 uppercase tracking-wider">Semantic Query</label>
      <div class="relative flex items-center bg-zinc-950/50 border border-zinc-800 rounded-xl shadow-lg focus-within:border-emerald-500/50 focus-within:ring-1 focus-within:ring-emerald-500/50 transition-all">
        <div class="pl-4 absolute flex items-center justify-center text-zinc-500">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
        </div>
        <input
          type="text"
          bind:value={appState.searchQuery}
          onkeydown={(e) => e.key === "Enter" && appState.handleSearch()}
          placeholder="Describe what you are looking for..."
          class="flex-1 bg-transparent pl-11 pr-5 py-3.5 text-zinc-100 placeholder-zinc-600 focus:outline-none"
        />
        <button
          onclick={() => appState.handleSearch()}
          disabled={!appState.searchQuery.trim() || appState.isSearching}
          class="px-5 py-2 mr-2 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/20 rounded-lg transition-colors font-medium text-sm disabled:opacity-30 flex items-center gap-2"
        >
          {#if appState.isSearching}
            <span class="w-4 h-4 rounded-full border-2 border-emerald-400 border-t-transparent animate-spin"></span>
            Executing...
          {:else}
            Search
          {/if}
        </button>
      </div>
    </div>

    <!-- Results Area -->
    <div class="flex-1 overflow-y-auto pr-2 pb-4">
      {#if appState.searchError}
        <div class="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl flex items-start gap-3">
          <svg class="w-5 h-5 text-rose-500 mt-0.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
          <p class="text-rose-400 text-sm">{appState.searchError}</p>
        </div>
      {/if}

      {#if appState.searchResults}
        <div class="space-y-4">
          <div class="flex items-center justify-between px-2">
            <h2 class="text-sm font-semibold text-zinc-400 tracking-wide">
              {appState.searchResults.total_results} MATCHES FOUND
            </h2>
          </div>

          <div class="grid grid-cols-1 gap-4">
            {#each appState.searchResults.results as result, i}
              <div class="group bg-zinc-900/30 border border-zinc-800/80 p-5 rounded-2xl hover:border-emerald-500/30 hover:bg-zinc-900/60 transition-all cursor-crosshair">
                <div class="flex justify-between items-start mb-3">
                  <span class="px-2.5 py-1 bg-zinc-800 text-zinc-400 rounded-md text-xs font-mono border border-zinc-700">Ref {i + 1}</span>
                  <div class="flex items-center gap-2 text-xs">
                    <span class="text-emerald-500/80 font-mono tracking-wider">Score</span>
                    <span class="text-zinc-300 font-medium">{result.score.toFixed(4)}</span>
                  </div>
                </div>
                <p class="text-[15px] leading-relaxed text-zinc-300 group-hover:text-zinc-200 transition-colors">
                  {result.text}
                </p>
              </div>
            {/each}
          </div>
        </div>
      {:else if !appState.isSearching && !appState.searchError}
        <div class="h-full flex items-center justify-center text-zinc-600">
          <p>Query the embedded space to retrieve context</p>
        </div>
      {/if}
    </div>
  </div>
</div>

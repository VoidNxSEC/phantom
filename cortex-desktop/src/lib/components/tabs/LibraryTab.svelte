<script lang="ts">
  import { appState } from "$lib/state.svelte";
</script>

<div class="flex-1 p-8 overflow-auto bg-[#0A0A0A] relative">
  <div class="absolute top-0 right-0 w-96 h-96 bg-yellow-500/5 rounded-full blur-[120px] pointer-events-none"></div>

  <header class="mb-8 z-10 shrink-0">
    <div class="flex items-center gap-4">
      <h1 class="text-3xl font-light text-white tracking-tight">Prompt Library</h1>
      <span class="px-3 py-1 bg-yellow-500/10 text-yellow-500 border border-yellow-500/20 rounded-full text-xs font-semibold tracking-wider">
        {appState.savedPrompts.length} SAVED
      </span>
    </div>
    <p class="text-zinc-500 text-sm mt-1">Versioned templates for retrieval and generation</p>
  </header>

  <div class="z-10">
    {#if appState.savedPrompts.length === 0}
      <div class="flex flex-col items-center justify-center p-20 border border-dashed border-zinc-800 rounded-3xl bg-zinc-900/30">
        <div class="w-16 h-16 bg-zinc-800/50 rounded-2xl flex items-center justify-center mb-6 shadow-inner border border-zinc-700/50">
          <svg class="w-8 h-8 text-zinc-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
        </div>
        <h3 class="text-xl font-medium text-zinc-300 mb-2">Library is empty</h3>
        <p class="text-zinc-500 text-sm mb-6">Create and test reliable prompts in the Workbench before saving them here.</p>
        <button
          onclick={() => appState.currentTab = "workbench"}
          class="px-5 py-2.5 bg-zinc-100 hover:bg-white text-zinc-900 rounded-xl font-medium transition-all shadow-[0_0_15px_rgba(255,255,255,0.1)] flex items-center gap-2"
        >
          Go to Workbench
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
        </button>
      </div>
    {:else}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each appState.savedPrompts as prompt (prompt.id)}
          <div class="group bg-zinc-900/30 border border-zinc-800/80 rounded-2xl p-6 hover:border-yellow-500/30 hover:bg-zinc-900/60 transition-all shadow-sm hover:shadow-xl relative overflow-hidden flex flex-col">
            <!-- Glow effect on hover -->
            <div class="absolute inset-0 bg-gradient-to-br from-yellow-500/0 to-yellow-500/0 group-hover:from-yellow-500/5 group-hover:to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"></div>

            <div class="flex justify-between items-start mb-4 z-10 relative">
              <h3 class="font-medium text-lg text-zinc-200 group-hover:text-yellow-100 transition-colors line-clamp-1 pr-4">{prompt.name}</h3>
              <button
                onclick={() => {
                  appState.savedPrompts = appState.savedPrompts.filter((p) => p.id !== prompt.id);
                  appState.savePrompts();
                }}
                class="text-zinc-600 hover:text-rose-400 p-1 bg-zinc-800/50 hover:bg-rose-500/10 rounded-lg transition-colors border border-transparent hover:border-rose-500/20"
                title="Delete Template"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              </button>
            </div>

            <div class="flex-1 bg-zinc-950 border border-zinc-800/80 rounded-xl p-4 mb-5 shadow-inner">
              <pre class="text-[13px] leading-relaxed text-zinc-400 font-mono whitespace-pre-wrap line-clamp-4">{prompt.template}</pre>
            </div>

            <div class="flex justify-between items-center z-10 relative shrink-0">
              <div class="flex gap-1.5 flex-wrap">
                {#each prompt.variables.slice(0, 2) as v}
                  <span class="px-2.5 py-1 bg-yellow-500/10 border border-yellow-500/20 text-yellow-400/90 rounded-md text-[11px] font-mono tracking-wide">{v}</span>
                {/each}
                {#if prompt.variables.length > 2}
                  <span class="px-2.5 py-1 bg-zinc-800 text-zinc-400 border border-zinc-700 rounded-md text-[11px] font-mono tracking-wide">
                    +{prompt.variables.length - 2}
                  </span>
                {/if}
              </div>
              <button
                onclick={() => {
                  appState.workbenchTemplate = prompt.template;
                  appState.currentTab = "workbench";
                }}
                class="text-sm font-medium text-zinc-400 hover:text-yellow-400 group/btn flex items-center gap-1.5 transition-colors"
              >
                Load
                <svg class="w-4 h-4 group-hover/btn:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

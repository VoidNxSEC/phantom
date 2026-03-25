<script lang="ts">
  import { appState } from "$lib/state.svelte";
</script>

<div class="flex-1 flex overflow-hidden bg-[#0A0A0A]">
  <!-- Left Side: Editor -->
  <div class="flex-1 flex flex-col p-8 border-r border-zinc-800/50 relative">
    <div class="absolute bottom-0 left-0 w-96 h-96 bg-fuchsia-500/5 rounded-full blur-[120px] pointer-events-none"></div>

    <header class="flex items-center justify-between mb-8 z-10 shrink-0">
      <div>
        <h1 class="text-3xl font-light text-white tracking-tight">Workbench</h1>
        <p class="text-zinc-500 text-sm mt-1">Prompt engineering & testing environment</p>
      </div>
      <div class="flex gap-3">
        <button
          onclick={() => appState.testPrompt()}
          class="px-5 py-2.5 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 hover:bg-zinc-800 text-zinc-300 rounded-xl font-medium transition-all shadow-sm flex items-center gap-2"
        >
          <svg class="w-4 h-4 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
          Render
        </button>
        <button
          onclick={() => appState.runWithLLM()}
          disabled={!appState.workbenchResult?.rendered || appState.isLoading}
          class="px-5 py-2.5 bg-zinc-100 hover:bg-white text-zinc-900 rounded-xl font-medium transition-all shadow-[0_0_15px_rgba(255,255,255,0.1)] disabled:opacity-50 disabled:shadow-none flex items-center gap-2"
        >
          <svg class="w-4 h-4 text-fuchsia-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
          Execute
        </button>
      </div>
    </header>

    <div class="flex-1 flex flex-col gap-6 overflow-hidden z-10">
      <div class="flex-1 flex flex-col">
        <div class="flex items-center justify-between mb-3">
          <label class="block text-xs font-semibold text-zinc-500 uppercase tracking-wider">Template String</label>
          <span class="text-xs text-zinc-600 font-mono">Syntax: {"{variable}"}</span>
        </div>
        <textarea
          bind:value={appState.workbenchTemplate}
          oninput={() => appState.updateWorkbenchVars()}
          placeholder="Context: {'{context}'}&#10;&#10;Question: {'{question}'}&#10;&#10;Answer:"
          class="flex-1 bg-zinc-900/50 border border-zinc-800 rounded-2xl p-5 font-mono text-[14px] leading-relaxed text-zinc-300 resize-none focus:outline-none focus:border-fuchsia-500/50 focus:ring-1 focus:ring-fuchsia-500/50 transition-all custom-scrollbar"
        ></textarea>
      </div>

      {#if Object.keys(appState.workbenchVars).length > 0}
        <div class="bg-zinc-900/30 border border-zinc-800/80 rounded-2xl p-5 shrink-0">
          <span class="block text-xs font-semibold text-zinc-500 mb-4 uppercase tracking-wider">Variables</span>
          <div class="space-y-3">
            {#each Object.entries(appState.workbenchVars) as [key, _]}
              <div class="flex gap-3 items-center">
                <span class="w-32 text-sm text-fuchsia-400 font-mono italic">{"{" + key + "}"}</span>
                <input
                  type="text"
                  bind:value={appState.workbenchVars[key]}
                  class="flex-1 bg-zinc-950/50 border border-zinc-800 rounded-xl px-4 py-2.5 text-sm text-zinc-200 focus:outline-none focus:border-fuchsia-500/50 transition-colors"
                  placeholder="Insert value for {key}"
                />
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <div class="flex gap-3 shrink-0">
        <input
          type="text"
          bind:value={appState.newPromptName}
          placeholder="Name this prompt schema..."
          class="flex-1 bg-zinc-900/50 border border-zinc-800 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-zinc-600 transition-colors"
        />
        <button
          onclick={() => {
            if (appState.newPromptName.trim() && appState.workbenchTemplate.trim()) {
              appState.savedPrompts = [
                {
                  id: `p_${Date.now()}`,
                  name: appState.newPromptName,
                  template: appState.workbenchTemplate,
                  variables: appState.extractVars(appState.workbenchTemplate),
                  created: new Date().toISOString(),
                },
                ...appState.savedPrompts,
              ];
              appState.savePrompts();
              appState.newPromptName = "";
            }
          }}
          disabled={!appState.newPromptName.trim() || !appState.workbenchTemplate.trim()}
          class="px-6 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded-xl text-sm font-medium transition-colors disabled:opacity-50"
        >
          Save to Library
        </button>
      </div>
    </div>
  </div>

  <!-- Right Side: Output Viewer -->
  <div class="w-[480px] flex flex-col p-8 overflow-hidden bg-zinc-950">
    <h2 class="text-sm font-semibold text-zinc-400 mb-6 uppercase tracking-wider">Evaluation Output</h2>

    {#if appState.workbenchResult}
      <div class="mb-5 p-4 border rounded-xl flex items-center justify-between {appState.workbenchResult.success ? 'bg-green-500/5 border-green-500/20' : 'bg-rose-500/5 border-rose-500/20'}">
        <div class="flex flex-col">
          <span class="text-xs text-zinc-500 uppercase tracking-wider mb-1">Status</span>
          <span class="text-sm font-medium {appState.workbenchResult.success ? 'text-green-400' : 'text-rose-400'}">
            {appState.workbenchResult.success ? "✓ Successful Compilation" : "✗ Rendering Error"}
          </span>
        </div>
        <div class="flex flex-col text-right">
          <span class="text-xs text-zinc-500 uppercase tracking-wider mb-1">Context Window</span>
          <span class="text-sm font-mono text-fuchsia-400">
            {appState.workbenchResult.tokens} tokens
          </span>
        </div>
      </div>

      <div class="flex-1 overflow-y-auto space-y-6 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent pr-2">
        <div>
          <span class="block text-xs font-semibold text-zinc-500 mb-3 uppercase tracking-wider">Payload Preview</span>
          <pre class="bg-zinc-900 border border-zinc-800/80 rounded-2xl p-5 text-[13px] text-zinc-300 font-mono whitespace-pre-wrap leading-relaxed shadow-inner">{appState.workbenchResult.rendered}</pre>
        </div>

        {#if appState.llmResponse || appState.isLoading}
          <div>
            <span class="block text-xs font-semibold text-zinc-500 mb-3 uppercase tracking-wider flex items-center gap-2">
              Neural Response
              {#if appState.isLoading}
                <span class="w-3 h-3 rounded-full border-[1.5px] border-fuchsia-500 border-t-transparent animate-spin"></span>
              {/if}
            </span>
            {#if appState.llmResponse && !appState.isLoading}
              <div class="bg-zinc-900 border border-zinc-800/80 rounded-2xl p-5 text-[14px] leading-relaxed text-zinc-200 whitespace-pre-wrap shadow-inner">
                {appState.llmResponse}
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {:else}
      <div class="flex-1 flex flex-col items-center justify-center text-zinc-600 border border-dashed border-zinc-800 rounded-2xl bg-zinc-900/30">
        <svg class="w-8 h-8 text-zinc-700 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
        <p class="text-sm">Render template to preview evaluation</p>
      </div>
    {/if}
  </div>
</div>

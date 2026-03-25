<script lang="ts">
  import { appState } from "$lib/state.svelte";
  import { onMount, tick } from "svelte";

  let chatContainer: HTMLElement;

  $effect(() => {
    // Scroll to bottom when messages change
    if (appState.messages.length) {
      tick().then(() => {
        if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
      });
    }
  });
</script>

<div class="flex-1 flex flex-col p-8 overflow-hidden h-full relative bg-[#0a0a0a]">
  <!-- Background Glow -->
  <div class="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-[120px] pointer-events-none"></div>

  <header class="flex items-center justify-between mb-8 z-10 shrink-0">
    <div>
      <h1 class="text-3xl font-light text-white tracking-tight">Chat</h1>
      <p class="text-zinc-500 text-sm mt-1">RAG-powered conversational interface</p>
    </div>
    <button
      onclick={() => appState.clearChat()}
      class="px-4 py-2 bg-zinc-900 border border-zinc-800 hover:border-zinc-700 hover:bg-zinc-800 text-zinc-300 rounded-xl text-sm transition-all shadow-sm"
    >
      Clear Context
    </button>
  </header>

  <div bind:this={chatContainer} class="flex-1 overflow-y-auto space-y-6 pr-4 z-10 scrollbar-thin scrollbar-thumb-zinc-800 scrollbar-track-transparent pb-4">
    {#if appState.messages.length === 0}
      <div class="h-full flex items-center justify-center text-zinc-600">
        <div class="text-center p-8 border border-zinc-800/50 rounded-2xl bg-zinc-900/20 backdrop-blur-sm">
          <div class="w-12 h-12 bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-4 border border-zinc-700/50">
            <svg class="w-6 h-6 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path></svg>
          </div>
          <p class="text-lg text-zinc-300">Start a conversation</p>
          <p class="text-sm mt-2 text-zinc-500">Ask the neural interface anything about the knowledge base.</p>
        </div>
      </div>
    {/if}

    {#each appState.messages as msg (msg.timestamp)}
      <div class="flex {msg.role === 'user' ? 'justify-end' : 'justify-start'} group">
        <div
          class="max-w-[80%] rounded-2xl px-6 py-4 shadow-sm relative {msg.role === 'user'
            ? 'bg-zinc-100 text-zinc-900 rounded-br-sm'
            : 'bg-zinc-900 text-zinc-100 border border-zinc-800/80 rounded-bl-sm'}"
        >
          <p class="whitespace-pre-wrap leading-relaxed text-[15px]">{msg.content}</p>
          
          {#if msg.sources?.length}
            <details class="mt-4 text-xs text-zinc-500 group-open:text-zinc-400 [&_summary::-webkit-details-marker]:hidden">
              <summary class="cursor-pointer select-none inline-flex items-center gap-1.5 hover:text-cyan-400 transition-colors">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                {msg.sources.length} Ref. Sources
              </summary>
              <div class="mt-3 space-y-2 border-t border-zinc-800 pt-3">
                {#each msg.sources as src}
                  <div class="pl-3 border-l-2 border-zinc-700 hover:border-cyan-500 transition-colors">
                    <p class="text-zinc-400 line-clamp-2">{src.text}</p>
                    <span class="text-[10px] text-zinc-600 mt-1 block">Score: {src.score.toFixed(3)}</span>
                  </div>
                {/each}
              </div>
            </details>
          {/if}
        </div>
      </div>
    {/each}

    {#if appState.isLoading}
      <div class="flex justify-start">
        <div class="bg-zinc-900 border border-zinc-800/80 rounded-2xl rounded-bl-sm px-6 py-5 flex items-center gap-2">
          <span class="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce"></span>
          <span class="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce" style="animation-delay: 0.15s"></span>
          <span class="w-1.5 h-1.5 bg-cyan-500 rounded-full animate-bounce" style="animation-delay: 0.3s"></span>
        </div>
      </div>
    {/if}
  </div>

  <div class="pt-4 z-10 shrink-0">
    <div class="relative flex items-center bg-zinc-900 border border-zinc-800 rounded-2xl shadow-lg focus-within:border-cyan-500/50 focus-within:ring-1 focus-within:ring-cyan-500/50 transition-all p-1">
      <input
        type="text"
        bind:value={appState.chatInput}
        onkeydown={(e) => e.key === "Enter" && appState.sendMessage()}
        placeholder="Ask anything..."
        class="flex-1 bg-transparent px-5 py-3.5 text-zinc-100 placeholder-zinc-600 focus:outline-none text-[15px]"
      />
      <button
        onclick={() => appState.sendMessage()}
        disabled={appState.isLoading || !appState.chatInput.trim()}
        class="absolute right-2 p-2.5 bg-zinc-100 hover:bg-white text-zinc-900 rounded-xl disabled:opacity-30 disabled:hover:bg-zinc-100 transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"></path>
        </svg>
      </button>
    </div>
    <p class="text-center text-xs text-zinc-600 mt-3 font-medium">Model: {appState.model} via {appState.provider}</p>
  </div>
</div>

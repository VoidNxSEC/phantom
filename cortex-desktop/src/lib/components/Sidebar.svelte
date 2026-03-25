<script lang="ts">
  import { appState } from "$lib/state.svelte";

  function navClass(tab: string): string {
    const base = "w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 relative group";
    if (appState.currentTab === tab) {
      return `${base} bg-zinc-800/80 text-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.1)] border border-zinc-700/50`;
    }
    return `${base} text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50 border border-transparent`;
  }
</script>

<nav class="w-16 bg-[#0a0a0a] border-r border-zinc-800/50 flex flex-col items-center py-5 gap-3 z-10 shrink-0">
  <!-- Logo Glow -->
  <div class="relative w-10 h-10 mb-4 group cursor-pointer flex items-center justify-center">
    <div class="absolute inset-0 bg-cyan-500/20 blur-xl rounded-full group-hover:bg-cyan-500/40 transition-all duration-500"></div>
    <div class="relative w-10 h-10 rounded-xl bg-gradient-to-br from-zinc-800 to-zinc-900 flex items-center justify-center border border-zinc-700/50 shadow-xl overflow-hidden">
      <div class="absolute inset-x-0 h-px top-0 bg-gradient-to-r from-transparent via-cyan-400/30 to-transparent"></div>
      <span class="text-lg font-bold bg-gradient-to-br from-white to-zinc-400 bg-clip-text text-transparent">C</span>
    </div>
  </div>

  <button onclick={() => (appState.currentTab = "chat")} class={navClass("chat")} title="Chat">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"></path>
    </svg>
  </button>

  <button onclick={() => (appState.currentTab = "process")} class={navClass("process")} title="Processing Pipeline">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path>
    </svg>
  </button>

  <button onclick={() => (appState.currentTab = "search")} class={navClass("search")} title="Vector Search">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
    </svg>
  </button>

  <button onclick={() => (appState.currentTab = "workbench")} class={navClass("workbench")} title="Prompt Workbench">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path>
    </svg>
  </button>

  <button onclick={() => (appState.currentTab = "library")} class={navClass("library")} title="Prompt Library">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
    </svg>
  </button>

  <button onclick={() => (appState.currentTab = "settings")} class={navClass("settings")} title="Settings">
    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path>
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
    </svg>
  </button>

  <div class="flex-1"></div>
  
  <div class="flex flex-col items-center justify-center gap-2 group">
    <div class="w-2.5 h-2.5 rounded-full {appState.apiStatus === 'online' ? 'bg-cyan-500 shadow-[0_0_8px_rgba(34,211,238,0.6)]' : appState.apiStatus === 'offline' ? 'bg-rose-500' : 'bg-amber-400 animate-pulse'}" title="API: {appState.apiStatus}"></div>
  </div>
</nav>

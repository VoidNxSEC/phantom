<script lang="ts">
  import { onMount } from "svelte";
  import { appState } from "$lib/state.svelte";
  
  import Sidebar from "$lib/components/Sidebar.svelte";
  import ChatTab from "$lib/components/tabs/ChatTab.svelte";
  import ProcessTab from "$lib/components/tabs/ProcessTab.svelte";
  import SearchTab from "$lib/components/tabs/SearchTab.svelte";
  import WorkbenchTab from "$lib/components/tabs/WorkbenchTab.svelte";
  import LibraryTab from "$lib/components/tabs/LibraryTab.svelte";
  import SettingsTab from "$lib/components/tabs/SettingsTab.svelte";

  onMount(() => {
    appState.loadFromStorage();
    appState.checkApi();
    appState.loadModels();
  });
</script>

<div class="h-screen flex bg-[#0A0A0A] text-zinc-300 overflow-hidden font-sans selection:bg-cyan-500/30">
  <Sidebar />

  <main class="flex-1 flex flex-col overflow-hidden relative shadow-[-10px_0_30px_rgba(0,0,0,0.5)] z-20 bg-[#0A0A0A]">
    {#if appState.currentTab === "chat"}
      <ChatTab />
    {:else if appState.currentTab === "process"}
      <ProcessTab />
    {:else if appState.currentTab === "search"}
      <SearchTab />
    {:else if appState.currentTab === "workbench"}
      <WorkbenchTab />
    {:else if appState.currentTab === "library"}
      <LibraryTab />
    {:else if appState.currentTab === "settings"}
      <SettingsTab />
    {/if}
  </main>
</div>

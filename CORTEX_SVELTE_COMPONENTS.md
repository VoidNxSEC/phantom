# CORTEX UI Components - Svelte Templates

## Sidebar.svelte
```svelte
<script lang="ts">
  export let settings: any;
  export let onUpdateSetting: (key: string, value: any) => void;
  export let onToggle: () => void;
  
  let models = $state<any>({});
  let showApiKeys = $state(false);
  
  async function loadModels() {
    try {
      const res = await fetch(`${settings.apiUrl}/api/models`);
      models = await res.json();
    } catch (e) {
      console.error('Failed to load models:', e);
    }
  }
</script>

<div class="w-80 h-screen bg-gray-900 border-r border-gray-800 flex flex-col">
  <div class="p-6 border-b border-gray-800">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-xl font-bold text-white">Settings</h2>
      <button onclick={onToggle} class="p-2 hover:bg-gray-800 rounded-lg">×</button>
    </div>
  </div>
  
  <div class="flex-1 overflow-y-auto p-6 space-y-6">
    <!-- Provider Selector -->
    <select bind:value={settings.provider} class="w-full bg-gray-800 text-white rounded-lg px-4 py-2">
      <option value="local">Local LLaMa</option>
      <option value="openai">OpenAI</option>
      <option value="anthropic">Anthropic</option>
    </select>
    
    <!-- Temperature Slider -->
    <div>
      <label class="text-sm text-gray-400">Temperature: {settings.temperature}</label>
      <input type="range" min="0" max="2" step="0.1" bind:value={settings.temperature} class="w-full" />
    </div>
    
    <!-- Top P Slider -->
    <div>
      <label class="text-sm text-gray-400">Top P: {settings.topP}</label>
      <input type="range" min="0" max="1" step="0.05" bind:value={settings.topP} class="w-full" />
    </div>
  </div>
</div>
```

## ChatView.svelte
```svelte
<script lang="ts">
  export let settings: any;
  
  let messages = $state([]);
  let input = $state('');
  let isLoading = $state(false);
  
  async function sendMessage() {
    if (!input.trim()) return;
    
    messages = [...messages, { role: 'user', content: input }];
    const question = input;
    input = '';
    isLoading = true;
    
    try {
      const res = await fetch(`${settings.apiUrl}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: question,
          conversation_id: 'demo',
          history: messages.slice(-10)
        })
      });
      
      const data = await res.json();
      messages = [...messages, data.message];
    } catch (e) {
      console.error(e);
    } finally {
      isLoading = false;
    }
  }
</script>

<div class="flex flex-col h-screen p-4">
  <div class="flex-1 overflow-y-auto space-y-4">
    {#each messages as msg}
      <div class:justify-end={msg.role === 'user'} class="flex">
        <div class="max-w-3xl rounded-2xl px-6 py-4"
             class:bg-cortex-600={msg.role === 'user'}
             class:bg-gray-800={msg.role === 'assistant'}>
          <p class="text-white">{msg.content}</p>
        </div>
      </div>
    {/each}
  </div>
  
  <div class="flex gap-3 mt-4">
    <textarea bind:value={input} placeholder="Ask anything..." class="flex-1 bg-gray-800 text-white rounded-xl px-4 py-3"></textarea>
    <button onclick={sendMessage} disabled={isLoading} class="px-6 bg-cortex-600 text-white rounded-xl">
      Send
    </button>
  </div>
</div>
```

## Installation Instructions

1. Copy these components to `cortex-desktop/src/lib/components/`
2. Ensure Tailwind is configured (already done)
3. Import in `+page.svelte`:

```typescript
import Sidebar from '$lib/components/Sidebar.svelte';
import ChatView from '$lib/components/ChatView.svelte';
```

## File Upload Component (Bonus)

```svelte
<script lang="ts">
  let uploading = $state(false);
  
  async function handleDrop(e: DragEvent) {
    e.preventDefault();
    const files = Array.from(e.dataTransfer?.files || []);
    
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    
    uploading = true;
    try {
      const res = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      console.log('Uploaded:', data);
    } finally {
      uploading = false;
    }
  }
</script>

<div ondrop={handleDrop} ondragover={(e) => e.preventDefault()} 
     class="border-2 border-dashed border-gray-600 rounded-xl p-12 text-center">
  <p class="text-gray-400">Drop files here to process</p>
</div>
```

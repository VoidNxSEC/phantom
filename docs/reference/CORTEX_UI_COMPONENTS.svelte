// CORTEX Desktop - UI Component Library
// Reusable Svelte components with Tailwind

// ═══════════════════════════════════════════════════════════════
// BUTTON COMPONENT
// ═══════════════════════════════════════════════════════════════

// src/lib/components/ui/Button.svelte
<script lang="ts">
  export let variant: 'primary' | 'secondary' | 'ghost' | 'danger' = 'primary';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let disabled = false;
  export let loading = false;
  
  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-700 hover:bg-gray-600 text-white',
    ghost: 'hover:bg-gray-800 text-gray-300',
    danger: 'bg-red-600 hover:bg-red-700 text-white'
  };
  
  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };
</script>

<button
  class="rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed {variants[variant]} {sizes[size]}"
  {disabled}
  on:click
>
  {#if loading}
    <span class="animate-spin">⟳</span>
  {:else}
    <slot />
  {/if}
</button>

// ═══════════════════════════════════════════════════════════════
// CARD COMPONENT
// ═══════════════════════════════════════════════════════════════

// src/lib/components/ui/Card.svelte
<script lang="ts">
  export let title: string | undefined = undefined;
  export let description: string | undefined = undefined;
</script>
d cortex-desktop
export PATH=$(echo $PATH | tr ':' '\n' | grep -v rustup | tr '\n' ':')
bun run tauri dev
<div class="bg-[#1a1a1a] border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors">
  {#if title}
    <h3 class="text-lg font-semibold mb-2">{title}</h3>
  {/if}
  
  {#if description}
    <p class="text-gray-400 text-sm mb-4">{description}</p>
  {/if}
  
  <slot />
</div>

// ═══════════════════════════════════════════════════════════════
// INPUT COMPONENT
// ═══════════════════════════════════════════════════════════════

// src/lib/components/ui/Input.svelte
<script lang="ts">
  export let value = '';
  export let type = 'text';
  export let placeholder = '';
  export let label: string | undefined = undefined;
  export let error: string | undefined = undefined;
</script>

<div class="flex flex-col gap-1.5">
  {#if label}
    <label class="text-sm font-medium text-gray-300">{label}</label>
  {/if}
  
  <input
    {type}
    {placeholder}
    bind:value
    class="bg-[#262626] border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500 transition-colors"
    class:border-red-500={error}
    on:input
    on:change
  />
  
  {#if error}
    <span class="text-red-500 text-sm">{error}</span>
  {/if}
</div>

//═══════════════════════════════════════════════════════════════
// SELECT/DROPDOWN COMPONENT
// ═══════════════════════════════════════════════════════════════

// src/lib/components/ui/Select.svelte
<script lang="ts">
  export let options: Array<{value: string, label: string}> = [];
  export let value: string;
  export let label: string | undefined = undefined;
  export let placeholder = 'Select...';
</script>

<div class="flex flex-col gap-1.5">
  {#if label}
    <label class="text-sm font-medium text-gray-300">{label}</label>
  {/if}
  
  <select
    bind:value
    class="bg-[#262626] border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500 transition-colors appearance-none"
    on:change
  >
    <option value="" disabled selected>{placeholder}</option>
    {#each options as option}
      <option value={option.value}>{option.label}</option>
    {/each}
  </select>
</div>

// ═══════════════════════════════════════════════════════════════
// SLIDER COMPONENT
// ═══════════════════════════════════════════════════════════════

// src/lib/components/ui/Slider.svelte
<script lang="ts">
  export let value = 0;
  export let min = 0;
  export let max = 100;
  export let step = 1;
  export let label: string | undefined = undefined;
  export let showValue = true;
</script>

<div class="flex flex-col gap-2">
  <div class="flex justify-between items-center">
    {#if label}
      <label class="text-sm font-medium text-gray-300">{label}</label>
    {/if}
    {#if showValue}
      <span class="text-sm text-gray-400">{value}</span>
    {/if}
  </div>
  
  <input
    type="range"
    bind:value
    {min}
    {max}
    {step}
    class="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
    on:input
    on:change
  />
</div>

// ═══════════════════════════════════════════════════════════════
// SWITCH/TOGGLE COMPONENT
// ═══════════════════════════════════════════════════════════════

// src/lib/components/ui/Switch.svelte
<script lang="ts">
  export let checked = false;
  export let label: string | undefined = undefined;
</script>

<label class="flex items-center gap-3 cursor-pointer">
  {#if label}
    <span class="text-sm font-medium text-gray-300">{label}</span>
  {/if}
  
  <div class="relative">
    <input
      type="checkbox"
      bind:checked
      class="sr-only peer"
      on:change
    />
    <div class="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:bg-blue-600 transition-colors"></div>
    <div class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full peer-checked:translate-x-5 transition-transform"></div>
  </div>
</label>

// ═══════════════════════════════════════════════════════════════
// DIALOG/MODAL COMPONENT
// ═══════════════════════════════════════════════════════════════

// src/lib/components/ui/Dialog.svelte
<script lang="ts">
  export let open = false;
  export let title: string | undefined = undefined;
  
  function close() {
    open = false;
  }
</script>

{#if open}
  <div class="fixed inset-0 z-50 flex items-center justify-center">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/70" on:click={close}></div>
    
    <!-- Dialog -->
    <div class="relative bg-[#1a1a1a] border border-gray-800 rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl">
      {#if title}
        <h2 class="text-xl font-semibold mb-4">{title}</h2>
      {/if}
      
      <slot />
      
      <div class="mt-6 flex justify-end gap-2">
        <slot name="actions" />
      </div>
    </div>
  </div>
{/if}

// ═══════════════════════════════════════════════════════════════
// BADGE COMPONENT
// ═══════════════════════════════════════════════════════════════

// src/lib/components/ui/Badge.svelte
<script lang="ts">
  export let variant: 'success' | 'error' | 'warning' | 'info' = 'info';
  
  const variants = {
    success: 'bg-green-900/30 text-green-400 border-green-700',
    error: 'bg-red-900/30 text-red-400 border-red-700',
    warning: 'bg-yellow-900/30 text-yellow-400 border-yellow-700',
    info: 'bg-blue-900/30 text-blue-400 border-blue-700'
  };
</script>

<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border {variants[variant]}">
  <slot />
</span>

// ═══════════════════════════════════════════════════════════════
// USAGE EXAMPLE
// ═══════════════════════════════════════════════════════════════

/*
<script>
  import { Button, Card, Input, Select, Slider, Switch, Dialog, Badge } from '$lib/components/ui';
  
  let temperature = 0.7;
  let provider = 'local';
  let dialogOpen = false;
</script>

<Card title="Model Configuration">
  <Select 
    label="Provider" 
    bind:value={provider}
    options={[
      {value: 'local', label: 'Local (LlamaCPP)'},
      {value: 'openai', label: 'OpenAI'},
      {value: 'anthropic', label: 'Anthropic'}
    ]}
  />
  
  <Slider 
    label="Temperature" 
    bind:value={temperature}
    min={0}
    max={2}
    step={0.1}
  />
  
  <Switch label="Enable streaming" checked/>
  
  <Button variant="primary" on:click={() => dialogOpen = true}>
    Save Configuration
  </Button>
</Card>

<Dialog bind:open={dialogOpen} title="Confirm Changes">
  <p>Save these model settings?</p>
  
  <svelte:fragment slot="actions">
    <Button variant="ghost" on:click={() => dialogOpen = false}>Cancel</Button>
    <Button variant="primary">Confirm</Button>
  </svelte:fragment>
</Dialog>
*/

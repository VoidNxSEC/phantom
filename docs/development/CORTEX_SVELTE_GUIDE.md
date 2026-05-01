# CORTEX v2.0 - Svelte Frontend Example

## 🎨 Svelte GUI Structure

This is a template for building a Svelte frontend to interact with CORTEX v2.0 API.

### Project Structure

```
cortex-svelte/
├── src/
│   ├── lib/
│   │   ├── api.ts              # API client
│   │   ├── stores.ts           # Svelte stores
│   │   └── components/
│   │       ├── DocumentUpload.svelte
│   │       ├── SemanticSearch.svelte
│   │       ├── InsightsViewer.svelte
│   │       └── RAGChat.svelte
│   ├── routes/
│   │   ├── +page.svelte        # Main dashboard
│   │   ├── search/
│   │   │   └── +page.svelte    # Search interface
│   │   └── rag/
│   │       └── +page.svelte    # RAG chat interface
│   └── app.html
├── static/
├── svelte.config.js
└── package.json
```

---

## 🚀 Quick Start

### 1. Create Svelte App with SvelteKit

```bash
npm create svelte@latest cortex-svelte
cd cortex-svelte
npm install

# Install additional dependencies
npm install @sveltejs/adapter-node
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 2. API Client (`src/lib/api.ts` )

```typescript
// API configuration
const API_BASE_URL = 'http://localhost:8000';

export interface ChunkRequest {
  text: string;
  chunk_size: number;
  chunk_overlap: number;
  strategy: string;
}

export interface SearchRequest {
  query: string;
  top_k: number;
}

export interface RAGRequest {
  question: string;
  context_size: number;
  llm_provider: string;
}

// API client
export class CortexAPI {
  async chunk(request: ChunkRequest) {
    const response = await fetch(`${API_BASE_URL}/api/chunk`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    return response.json();
  }

  async search(request: SearchRequest) {
    const response = await fetch(`${API_BASE_URL}/api/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    return response.json();
  }

  async process(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/process`, {
      method: 'POST',
      body: formData
    });
    return response.json();
  }

  async rag(request: RAGRequest) {
    const response = await fetch(`${API_BASE_URL}/api/rag`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
    return response.json();
  }
}

export const api = new CortexAPI();
```

### 3. Document Upload Component

```svelte
<!-- src/lib/components/DocumentUpload.svelte -->
<script lang="ts">
  import { api } from '$lib/api';
  
  let uploading = false;
  let insights: any = null;
  let error: string | null = null;

  async function handleUpload(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    
    if (!file) return;
    
    uploading = true;
    error = null;
    
    try {
      const result = await api.process(file);
      insights = result.insights;
    } catch (e) {
      error = e.message;
    } finally {
      uploading = false;
    }
  }
</script>

<div class="upload-container">
  <h2>Upload Markdown Document</h2>
  
  <input 
    type="file" 
    accept=".md" 
    on:change={handleUpload}
    disabled={uploading}
  />
  
  {#if uploading}
    <div class="loading">Processing...</div>
  {/if}
  
  {#if error}
    <div class="error">{error}</div>
  {/if}
  
  {#if insights}
    <div class="insights">
      <h3>Extracted Insights</h3>
      
      <section>
        <h4>Themes ({insights.themes.length})</h4>
        {#each insights.themes as theme}
          <div class="card">
            <strong>{theme.title}</strong>
            <p>{theme.description}</p>
          </div>
        {/each}
      </section>
      
      <!-- Add more sections for patterns, learnings, etc. -->
    </div>
  {/if}
</div>

<style>
  .upload-container {
    padding: 2rem;
    max-width: 800px;
    margin: 0 auto;
  }
  
  .card {
    background: #f5f5f5;
    padding: 1rem;
    margin: 0.5rem 0;
    border-radius: 8px;
  }
  
  .loading {
    color: #0066cc;
    margin: 1rem 0;
  }
  
  .error {
    color: #cc0000;
    margin: 1rem 0;
  }
</style>
```

### 4. RAG Chat Interface

```svelte
<!-- src/lib/components/RAGChat.svelte -->
<script lang="ts">
  import { api } from '$lib/api';
  
  let question = '';
  let messages: Array<{type: 'user' | 'assistant', text: string, sources?: any[]}> = [];
  let loading = false;

  async function askQuestion() {
    if (!question.trim()) return;
    
    const userMsg = { type: 'user', text: question };
    messages = [...messages, userMsg];
    
    const currentQuestion = question;
    question = '';
    loading = true;
    
    try {
      const response = await api.rag({
        question: currentQuestion,
        context_size: 5,
        llm_provider: 'local'
      });
      
      messages = [...messages, {
        type: 'assistant',
        text: response.answer,
        sources: response.sources
      }];
    } catch (e) {
      messages = [...messages, {
        type: 'assistant',
        text: 'Error: ' + e.message
      }];
    } finally {
      loading = false;
    }
  }
</script>

<div class="chat-container">
  <div class="messages">
    {#each messages as msg}
      <div class="message {msg.type}">
        <div class="content">{msg.text}</div>
        
        {#if msg.sources}
          <details class="sources">
            <summary>Sources ({msg.sources.length})</summary>
            {#each msg.sources as source}
              <div class="source">
                Score: {source.score.toFixed(3)}<br/>
                {source.text}
              </div>
            {/each}
          </details>
        {/if}
      </div>
    {/each}
    
    {#if loading}
      <div class="message assistant loading">
        Thinking...
      </div>
    {/if}
  </div>
  
  <form on:submit|preventDefault={askQuestion} class="input-form">
    <input 
      type="text" 
      bind:value={question}
      placeholder="Ask a question..."
      disabled={loading}
    />
    <button type="submit" disabled={loading || !question.trim()}>
      Send
    </button>
  </form>
</div>

<style>
  .chat-container {
    display: flex;
    flex-direction: column;
    height: 600px;
    border: 1px solid #ddd;
    border-radius: 8px;
  }
  
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }
  
  .message {
    margin: 0.5rem 0;
    padding: 0.75rem;
    border-radius: 8px;
    max-width: 80%;
  }
  
  .message.user {
    background: #0066cc;
    color: white;
    margin-left: auto;
  }
  
  .message.assistant {
    background: #f0f0f0;
  }
  
  .sources {
    margin-top: 0.5rem;
    font-size: 0.85em;
  }
  
  .input-form {
    display: flex;
    padding: 1rem;
    border-top: 1px solid #ddd;
  }
  
  .input-form input {
    flex: 1;
    padding: 0.5rem;
    border: 1px solid #ddd;
    border-radius: 4px;
  }
  
  .input-form button {
    margin-left: 0.5rem;
    padding: 0.5rem 1rem;
    background: #0066cc;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
</style>
```

---

## 🔌 Running the Stack

### Terminal 1: CORTEX API Server
```bash
cd phantom
nix develop --command uvicorn cortex_api:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: LlamaCPP Server (for RAG)
```bash
python -m llama_cpp.server --model modelo.gguf --port 8080
```

### Terminal 3: Svelte Dev Server
```bash
cd cortex-svelte
npm run dev
```

---

## 📡 API Endpoints

### Process Document
```typescript
POST /api/process
Content-Type: multipart/form-data

// Response:
{
  "success": true,
  "file_name": "document.md",
  "insights": {
    "themes": [...],
    "patterns": [...],
    "learnings": [...],
    ...
  }
}
```

### Semantic Search
```typescript
POST /api/search
Content-Type: application/json

{
  "query": "error handling",
  "top_k": 5
}

// Response:
{
  "results": [
    {
      "chunk_id": 0,
      "text": "...",
      "score": 0.89
    }
  ]
}
```

### RAG Query
```typescript
POST /api/rag
Content-Type: application/json

{
  "question": "How to handle errors?",
  "context_size": 5,
  "llm_provider": "local"
}

// Response:
{
  "answer": "...",
  "sources": [...]
}
```

---

## 🎨 Styling with Tailwind

```svelte
<!-- Example with Tailwind -->
<div class="max-w-4xl mx-auto p-6">
  <h1 class="text-3xl font-bold text-gray-900 mb-8">
    CORTEX Dashboard
  </h1>
  
  <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    <div class="bg-white rounded-lg shadow p-6">
      <!-- Content -->
    </div>
  </div>
</div>
```

---

## 🔐 Production Considerations

1. **CORS**: Configure allowed origins properly
2. **Authentication**: Add JWT/OAuth
3. **Rate Limiting**: Protect API endpoints
4. **Error Handling**: Better error messages
5. **Logging**: Request/response logging
6. **Monitoring**: Add Prometheus metrics

---

## 📚 Next Steps

1. Implement all components
2. Add state management (Svelte stores)
3. Add real-time updates (WebSockets)
4. Deploy with Docker Compose
5. Add analytics dashboard

---

**Ready to build!** 🚀

Start the API server and begin integrating with your Svelte frontend!

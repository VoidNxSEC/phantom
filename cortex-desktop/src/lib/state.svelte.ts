import { processDocument, searchVectors, type ProcessDocumentResponse } from "$lib/api";

export interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  timestamp: number;
}

export interface Source {
  id: number;
  text: string;
  score: number;
}

export interface PromptTemplate {
  id: string;
  name: string;
  template: string;
  variables: string[];
  created: string;
}

export class CortexState {
  currentTab = $state<"chat" | "process" | "search" | "workbench" | "library" | "settings">("chat");
  apiUrl = $state("http://localhost:8087");
  provider = $state("tensor_forge");
  model = $state("/L3-8B-Stheno-v3.2-Q4_K_S.gguf");
  temperature = $state(0.7);
  maxTokens = $state(2048);

  messages = $state<Message[]>([]);
  chatInput = $state("");
  isLoading = $state(false);
  conversationId = $state("");

  workbenchTemplate = $state("");
  workbenchVars = $state<Record<string, string>>({});
  workbenchResult = $state<any>(null);
  llmResponse = $state("");

  savedPrompts = $state<PromptTemplate[]>([]);
  newPromptName = $state("");

  apiStatus = $state<"online" | "offline" | "checking">("checking");
  availableModels = $state<Record<string, any[]>>({});

  uploadedFiles = $state<{ name: string; status: string }[]>([]);
  isDragging = $state(false);

  selectedFile = $state<File | null>(null);
  chunkStrategy = $state<"recursive" | "sliding" | "simple">("recursive");
  chunkSize = $state(1024);
  isProcessing = $state(false);
  processResult = $state<ProcessDocumentResponse | null>(null);
  processError = $state("");

  searchQuery = $state("");
  searchResults = $state<any>(null);
  isSearching = $state(false);
  searchError = $state("");

  constructor() {
    this.conversationId = `conv_${Date.now()}`;
  }

  loadFromStorage() {
    try {
      if (typeof window === "undefined") return;
      const s = localStorage.getItem("cortex_settings");
      if (s) {
        const data = JSON.parse(s);
        this.apiUrl = data.apiUrl || this.apiUrl;
        this.provider = data.provider || this.provider;
        this.model = data.model || this.model;
        this.temperature = data.temperature ?? this.temperature;
        this.maxTokens = data.maxTokens || this.maxTokens;
      }
      const p = localStorage.getItem("cortex_prompts");
      if (p) this.savedPrompts = JSON.parse(p);
    } catch { }
  }

  saveSettings() {
    if (typeof window === "undefined") return;
    localStorage.setItem(
      "cortex_settings",
      JSON.stringify({ apiUrl: this.apiUrl, provider: this.provider, model: this.model, temperature: this.temperature, maxTokens: this.maxTokens })
    );
  }

  savePrompts() {
    if (typeof window === "undefined") return;
    localStorage.setItem("cortex_prompts", JSON.stringify(this.savedPrompts));
  }

  async checkApi() {
    this.apiStatus = "checking";
    try {
      const res = await fetch(`${this.apiUrl}/health`);
      this.apiStatus = res.ok ? "online" : "offline";
    } catch {
      this.apiStatus = "offline";
    }
  }

  async loadModels() {
    try {
      const res = await fetch(`${this.apiUrl}/api/models`);
      if (res.ok) this.availableModels = await res.json();
    } catch { }
  }

  // Chat actions
  async sendMessage() {
    if (!this.chatInput.trim() || this.isLoading) return;

    this.messages = [
      ...this.messages,
      { role: "user", content: this.chatInput.trim(), timestamp: Date.now() },
    ];
    const question = this.chatInput;
    this.chatInput = "";
    this.isLoading = true;

    try {
      const res = await fetch(`${this.apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: question,
          conversation_id: this.conversationId,
          history: this.messages
            .slice(-10)
            .map((m) => ({ role: m.role, content: m.content })),
          context_size: 5,
          llm_provider: this.provider,
          model: this.model,
          temperature: this.temperature,
          max_tokens: this.maxTokens,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        this.messages = [
          ...this.messages,
          {
            role: "assistant",
            content: data.message.content,
            sources: data.message.sources,
            timestamp: Date.now(),
          },
        ];
      } else {
        let errorDetail = `HTTP ${res.status}`;
        try {
          const errBody = await res.json();
          errorDetail = errBody.detail || errBody.message || JSON.stringify(errBody);
        } catch { errorDetail = await res.text().catch(() => errorDetail); }
        this.messages = [
          ...this.messages,
          { role: "assistant", content: `❌ API Error: ${errorDetail}`, timestamp: Date.now() },
        ];
      }
    } catch {
      this.messages = [
        ...this.messages,
        {
          role: "assistant",
          content: "❌ Connection failed",
          timestamp: Date.now(),
        },
      ];
    }
    this.isLoading = false;
  }

  clearChat() {
    this.messages = [];
    this.conversationId = `conv_${Date.now()}`;
  }

  // Workbench Actions
  extractVars(t: string): string[] {
    const m = t.match(/\{(\w+)\}/g) || [];
    return [...new Set(m.map((x) => x.slice(1, -1)))];
  }

  updateWorkbenchVars() {
    const vars = this.extractVars(this.workbenchTemplate);
    const newVars: Record<string, string> = {};
    vars.forEach((v) => (newVars[v] = this.workbenchVars[v] || ""));
    this.workbenchVars = newVars;
  }

  async testPrompt() {
    try {
      const res = await fetch(`${this.apiUrl}/api/prompt/test`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          template: this.workbenchTemplate,
          variables: this.workbenchVars,
        }),
      });
      if (res.ok) this.workbenchResult = await res.json();
    } catch { }
  }

  async runWithLLM() {
    if (!this.workbenchResult?.rendered) return;
    this.isLoading = true;
    try {
      const res = await fetch(`${this.apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: this.workbenchResult.rendered,
          conversation_id: "workbench",
          history: [],
          context_size: 0,
          llm_provider: this.provider,
          model: this.model,
          temperature: this.temperature,
          max_tokens: this.maxTokens,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        this.llmResponse = data.message.content;
      }
    } catch { }
    this.isLoading = false;
  }

  // File Upload
  async handleDrop(e: DragEvent) {
    e.preventDefault();
    this.isDragging = false;
    const files = Array.from(e.dataTransfer?.files || []);
    if (!files.length) return;

    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));

    this.uploadedFiles = [
      ...this.uploadedFiles,
      ...files.map((f) => ({ name: f.name, status: "uploading" })),
    ];

    try {
      const res = await fetch(`${this.apiUrl}/api/upload`, {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        this.uploadedFiles = this.uploadedFiles.map((f) => {
          const r = data.files?.find((x: any) => x.filename === f.name);
          return r ? { ...f, status: r.status } : f;
        });
      }
    } catch {
      this.uploadedFiles = this.uploadedFiles.map((f) =>
        f.status === "uploading" ? { ...f, status: "error" } : f,
      );
    }
  }

  // Processing
  async handleProcess() {
    if (!this.selectedFile) {
      this.processError = "Please select a file first";
      return;
    }

    this.isProcessing = true;
    this.processError = "";
    this.processResult = null;

    try {
      const response = await processDocument({
        file: this.selectedFile,
        chunkStrategy: this.chunkStrategy,
        chunkSize: this.chunkSize,
      });
      this.processResult = response;
    } catch (e: any) {
      this.processError = e.message || "Processing failed";
    } finally {
      this.isProcessing = false;
    }
  }

  // Vector Search
  async handleSearch() {
    if (!this.searchQuery.trim()) {
      this.searchError = "Please enter a search query";
      return;
    }

    this.isSearching = true;
    this.searchError = "";
    this.searchResults = null;

    try {
      const response = await searchVectors({ query: this.searchQuery, topK: 5 });
      this.searchResults = response;
    } catch (e: any) {
      this.searchError = e.message || "Search failed";
    } finally {
      this.isSearching = false;
    }
  }
}

// Global Singleton Instance
export const appState = new CortexState();

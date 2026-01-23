<script lang="ts">
    import { processDocument, type ProcessDocumentResponse } from "$lib/api";

    // State
    let selectedFile = $state<File | null>(null);
    let chunkStrategy = $state<"recursive" | "sliding" | "simple">("recursive");
    let chunkSize = $state(1024);
    let isProcessing = $state(false);
    let result = $state<ProcessDocumentResponse | null>(null);
    let error = $state("");

    // File selection
    function handleFileSelect(e: Event) {
        const input = e.target as HTMLInputElement;
        if (input.files?.[0]) {
            selectedFile = input.files[0];
            result = null;
            error = "";
        }
    }

    // Process document
    async function handleProcess() {
        if (!selectedFile) {
            error = "Please select a file first";
            return;
        }

        isProcessing = true;
        error = "";
        result = null;

        try {
            const response = await processDocument({
                file: selectedFile,
                chunkStrategy,
                chunkSize,
            });
            result = response;
        } catch (e: any) {
            error = e.message || "Processing failed";
        } finally {
            isProcessing = false;
        }
    }
</script>

<div class="flex-1 flex flex-col p-6 overflow-hidden">
    <header class="mb-6">
        <h1 class="text-2xl font-bold">Document Processing</h1>
        <p class="text-gray-500 text-sm">
            Extract insights from documents using CORTEX
        </p>
    </header>

    <div class="flex-1 flex flex-col overflow-hidden space-y-6">
        <!-- Upload Section -->
        <div class="space-y-4">
            <div>
                <label
                    for="file-input"
                    class="block text-sm font-medium text-gray-400 mb-2"
                >
                    Document File
                </label>
                <input
                    id="file-input"
                    type="file"
                    accept=".md,.txt"
                    onchange={handleFileSelect}
                    class="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-cyan-600 file:text-white hover:file:bg-cyan-700 bg-gray-800 rounded-xl border border-gray-700"
                />
                {#if selectedFile}
                    <p class="mt-2 text-sm text-gray-400">
                        Selected: {selectedFile.name}
                    </p>
                {/if}
            </div>

            <div class="grid grid-cols-2 gap-4">
                <div>
                    <label
                        for="chunk-strategy"
                        class="block text-sm font-medium text-gray-400 mb-2"
                    >
                        Chunking Strategy
                    </label>
                    <select
                        id="chunk-strategy"
                        bind:value={chunkStrategy}
                        class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 focus:outline-none focus:border-cyan-500"
                    >
                        <option value="recursive">Recursive</option>
                        <option value="sliding">Sliding Window</option>
                        <option value="simple">Simple</option>
                    </select>
                </div>

                <div>
                    <label
                        for="chunk-size"
                        class="block text-sm font-medium text-gray-400 mb-2"
                    >
                        Chunk Size (tokens)
                    </label>
                    <input
                        id="chunk-size"
                        type="number"
                        min="256"
                        max="2048"
                        step="128"
                        bind:value={chunkSize}
                        class="w-full bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 focus:outline-none focus:border-cyan-500"
                    />
                </div>
            </div>

            <button
                onclick={handleProcess}
                disabled={!selectedFile || isProcessing}
                class="w-full py-3 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-xl font-medium disabled:opacity-50 hover:from-cyan-500 hover:to-blue-500 transition-all"
            >
                {isProcessing ? "Processing..." : "Process Document"}
            </button>
        </div>

        <!-- Results Section -->
        {#if error}
            <div class="p-4 bg-red-900/20 border border-red-500 rounded-xl">
                <p class="text-red-400">❌ {error}</p>
            </div>
        {/if}

        {#if result}
            <div class="flex-1 overflow-auto space-y-4">
                <div
                    class="p-4 bg-gray-800/50 rounded-xl border border-gray-700"
                >
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="text-lg font-semibold">Processing Result</h2>
                        <span class="text-sm text-gray-400">
                            {result.processing_time.toFixed(2)}s
                        </span>
                    </div>

                    <div class="space-y-3">
                        <div>
                            <span class="text-sm text-gray-400">File:</span>
                            <span class="ml-2 font-mono text-cyan-400"
                                >{result.filename}</span
                            >
                        </div>

                        {#if result.insights?.themes}
                            <div>
                                <h3
                                    class="text-sm font-medium text-gray-400 mb-2"
                                >
                                    Themes Extracted
                                </h3>
                                <div class="space-y-2">
                                    {#each result.insights.themes as theme}
                                        <div
                                            class="p-3 bg-gray-900 rounded-lg border-l-4 border-cyan-500"
                                        >
                                            <div
                                                class="flex justify-between items-start"
                                            >
                                                <h4
                                                    class="font-semibold text-white"
                                                >
                                                    {theme.title}
                                                </h4>
                                                <span
                                                    class="px-2 py-0.5 text-xs rounded {theme.confidence ===
                                                    'high'
                                                        ? 'bg-green-500/20 text-green-400'
                                                        : theme.confidence ===
                                                            'medium'
                                                          ? 'bg-yellow-500/20 text-yellow-400'
                                                          : 'bg-gray-500/20 text-gray-400'}"
                                                >
                                                    {theme.confidence}
                                                </span>
                                            </div>
                                            <p
                                                class="mt-1 text-sm text-gray-400"
                                            >
                                                {theme.description}
                                            </p>
                                        </div>
                                    {/each}
                                </div>
                            </div>
                        {/if}
                    </div>
                </div>
            </div>
        {/if}

        {#if isProcessing}
            <div class="flex items-center justify-center p-8">
                <div class="flex gap-1">
                    <span
                        class="w-3 h-3 bg-cyan-500 rounded-full animate-bounce"
                    ></span>
                    <span
                        class="w-3 h-3 bg-cyan-500 rounded-full animate-bounce"
                        style="animation-delay: 0.1s"
                    ></span>
                    <span
                        class="w-3 h-3 bg-cyan-500 rounded-full animate-bounce"
                        style="animation-delay: 0.2s"
                    ></span>
                </div>
            </div>
        {/if}
    </div>
</div>

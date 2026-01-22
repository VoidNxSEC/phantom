<script lang="ts">
    import "../app.css";
    import { onMount } from "svelte";
    import type { Snippet } from "svelte";

    // Props
    interface Props {
        children?: Snippet;
    }
    let { children }: Props = $props();

    // Theme management
    let isDark = $state(true);

    onMount(() => {
        // Check system preference
        isDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
        updateTheme();
    });

    function toggleTheme() {
        isDark = !isDark;
        updateTheme();
    }

    function updateTheme() {
        if (isDark) {
            document.documentElement.classList.add("dark");
        } else {
            document.documentElement.classList.remove("dark");
        }
    }
</script>

<div
    class="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-950 dark:to-gray-900 transition-colors duration-300"
>
    <!-- Theme Toggle -->
    <button
        onclick={toggleTheme}
        class="fixed top-4 right-4 z-50 p-3 rounded-full glass-dark hover:scale-110 transition-transform duration-200"
        aria-label="Toggle theme"
    >
        {#if isDark}
            <svg
                class="w-5 h-5 text-yellow-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
                ></path>
            </svg>
        {:else}
            <svg
                class="w-5 h-5 text-gray-700"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
                ></path>
            </svg>
        {/if}
    </button>

    <!-- Main Content -->
    {@render children?.()}
</div>

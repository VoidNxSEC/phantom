# CORTEX Desktop - Quick Start Guide

## 🚀 Create Project

```bash
cd /home/kernelcore/dev/Projects/phantom

# Create Tauri + Svelte project
npm create tauri-app@latest cortex-desktop

# Choose:
# - Package manager: npm
# - UI template: Svelte
# - Language: TypeScript
# - UI flavor: SvelteKit
```

---

## 📦 Installation

```bash
cd cortex-desktop

# Install dependencies
npm install

# Install additional packages
npm install -D @sveltejs/adapter-static
npm install -D tailwindcss postcss autoprefixer
npm install -D @tauri-apps/api
npm install lucide-svelte  # Icons
npm install clsx tailwind-merge  # Utility

# Initialize Tailwind
npx tailwindcss init -p
```

---

## 🔧 Configuration Files

### `tailwind.config.js`
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: {
          primary: '#0f0f0f',
          secondary: '#1a1a1a',
          tertiary: '#262626',
        },
        text: {
          primary: '#ffffff',
          secondary: '#a3a3a3',
        },
        accent: {
          blue: '#3b82f6',
          purple: '#8b5cf6',
        }
      }
    },
  },
  plugins: [],
}
```

### `src/app.css`
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --bg-primary: 15 15 15;
    --bg-secondary: 26 26 26;
    --bg-tertiary: 38 38 38;
    --text-primary: 255 255 255;
    --text-secondary: 163 163 163;
  }
  
  * {
    @apply border-gray-800;
  }
  
  body {
    @apply bg-[rgb(var(--bg-primary))] text-[rgb(var(--text-primary))];
    font-family: 'Inter', system-ui, sans-serif;
  }
}

@layer components {
  .btn-primary {
    @apply px-4 py-2 bg-accent-blue hover:bg-blue-600 rounded-lg transition-colors;
  }
  
  .card {
    @apply bg-[rgb(var(--bg-secondary))] rounded-xl border border-gray-800 p-6;
  }
}
```

### `src-tauri/tauri.conf.json` (Key sections)
```json
{
  "build": {
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build",
    "devPath": "http://localhost:5173",
    "distDir": "../build"
  },
  "package": {
    "productName": "CORTEX Desktop",
    "version": "2.0.0"
  },
  "tauri": {
    "allowlist": {
      "all": false,
      "shell": {
        "all": false,
        "open": true
      },
      "fs": {
        "all": false,
        "readFile": true,
        "writeFile": true,
        "readDir": true,
        "scope": ["$APPDATA/*", "$DOCUMENT/*"]
      },
      "dialog": {
        "all": true
      },
      "http": {
        "all": true,
        "scope": ["http://localhost:8000/*"]
      }
    },
    "windows": [
      {
        "title": "CORTEX Desktop",
        "width": 1400,
        "height": 900,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "fullscreen": false
      }
    ]
  }
}
```

---

## 🏃 Run Development

```bash
# Terminal 1: CORTEX API (backend)
cd /home/kernelcore/dev/Projects/phantom
nix develop --command uvicorn cortex_api:app --reload

# Terminal 2: Tauri app
cd cortex-desktop
npm run tauri dev
```

---

## 🏗️ Build for Production

```bash
npm run tauri build

# Output:
# src-tauri/target/release/bundle/deb/cortex-desktop_2.0.0_amd64.deb
# src-tauri/target/release/bundle/appimage/cortex-desktop_2.0.0_amd64.AppImage
```

---

## 📁 Project Structure Created

```
cortex-desktop/
├── src/
│   ├── routes/
│   │   ├── +layout.svelte       # Root layout
│   │   ├── +page.svelte         # Dashboard
│   │   ├── chat/+page.svelte    # Chat interface
│   │   └── settings/+page.svelte # Settings
│   ├── lib/
│   │   ├── components/
│   │   │   └── ui/              # UI components
│   │   ├── stores/              # State management
│   │   └── api/                 # API clients
│   └── app.css
├── src-tauri/
│   ├── src/
│   │   ├── main.rs
│   │   ├── api.rs
│   │   └── config.rs
│   └── Cargo.toml
└── package.json
```

---

## 🎨 Next Steps

1. Implement UI components
2. Create Tauri commands (Rust)
3. Build chat interface
4. Add settings page
5. Connect to CORTEX API

---

Ready to start development! 🚀

// CORTEX Desktop - Rust Backend (Tauri Commands)
// src-tauri/src/main.rs

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use serde::{Deserialize, Serialize};
use std::sync::Mutex;
use tauri::State;

// ═══════════════════════════════════════════════════════════════
// DATA STRUCTURES
// ═══════════════════════════════════════════════════════════════

#[derive(Debug, Serialize, Deserialize, Clone)]
struct AppConfig {
    providers: Vec<Provider>,
    active_provider: String,
    api_keys: std::collections::HashMap<String, String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct Provider {
    name: String,
    provider_type: String, // "local" | "openai" | "anthropic"
    base_url: Option<String>,
    model: String,
    parameters: ModelParameters,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
struct ModelParameters {
    temperature: f32,
    top_p: f32,
    max_tokens: u32,
    context_size: u32,
}

#[derive(Debug, Serialize, Deserialize)]
struct SystemStats {
    vram_total_mb: u64,
    vram_used_mb: u64,
    vram_free_mb: u64,
    ram_total_mb: u64,
    ram_used_mb: u64,
    cpu_usage_percent: f32,
}

#[derive(Debug, Serialize, Deserialize)]
struct ProcessDocumentRequest {
    file_path: String,
    chunk_size: u32,
    enable_embeddings: bool,
}

#[derive(Debug, Serialize, Deserialize)]
struct RAGQueryRequest {
    question: String,
    context_size: u32,
    llm_provider: String,
}

// ═══════════════════════════════════════════════════════════════
// TAURI COMMANDS
// ═══════════════════════════════════════════════════════════════

#[tauri::command]
async fn process_document(request: ProcessDocumentRequest) -> Result<String, String> {
    // Call CORTEX API endpoint
    let client = reqwest::Client::new();
    
    // Build multipart form
    let form = reqwest::multipart::Form::new()
        .file("file", &request.file_path)
        .await
        .map_err(|e| e.to_string())?;
    
    let res = client
        .post("http://localhost:8000/api/process")
        .multipart(form)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    let body = res.text().await.map_err(|e| e.to_string())?;
    Ok(body)
}

#[tauri::command]
async fn semantic_search(query: String, top_k: u32) -> Result<String, String> {
    let client = reqwest::Client::new();
    
    let request_body = serde_json::json!({
        "query": query,
        "top_k": top_k
    });
    
    let res = client
        .post("http://localhost:8000/api/search")
        .json(&request_body)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    let body = res.text().await.map_err(|e| e.to_string())?;
    Ok(body)
}

#[tauri::command]
async fn rag_query(request: RAGQueryRequest) -> Result<String, String> {
    let client = reqwest::Client::new();
    
    let request_body = serde_json::json!({
        "question": request.question,
        "context_size": request.context_size,
        "llm_provider": request.llm_provider
    });
    
    let res = client
        .post("http://localhost:8000/api/rag")
        .json(&request_body)
        .send()
        .await
        .map_err(|e| e.to_string())?;
    
    let body = res.text().await.map_err(|e| e.to_string())?;
    Ok(body)
}

#[tauri::command]
fn get_system_stats() -> Result<SystemStats, String> {
    // Get VRAM stats using nvidia-smi
    let vram = get_vram_info()?;
    
    // Get RAM stats using sysinfo
    use sysinfo::{System, SystemExt};
    let mut sys = System::new_all();
    sys.refresh_all();
    
    Ok(SystemStats {
        vram_total_mb: vram.0,
        vram_used_mb: vram.1,
        vram_free_mb: vram.2,
        ram_total_mb: sys.total_memory() / 1024 / 1024,
        ram_used_mb: sys.used_memory() / 1024 / 1024,
        cpu_usage_percent: sys.global_cpu_info().cpu_usage(),
    })
}

#[tauri::command]
fn save_config(config: AppConfig, state: State<Mutex<AppConfig>>) -> Result<(), String> {
    let mut app_config = state.lock().unwrap();
    *app_config = config;
    
    // Persist to file
    let config_path = get_config_path();
    let json = serde_json::to_string_pretty(&*app_config).map_err(|e| e.to_string())?;
    std::fs::write(config_path, json).map_err(|e| e.to_string())?;
    
    Ok(())
}

#[tauri::command]
fn load_config(state: State<Mutex<AppConfig>>) -> Result<AppConfig, String> {
    let config = state.lock().unwrap();
    Ok(config.clone())
}

#[tauri::command]
async fn health_check() -> Result<bool, String> {
    let client = reqwest::Client::new();
    
    match client.get("http://localhost:8000/health").send().await {
        Ok(res) => Ok(res.status().is_success()),
        Err(_) => Ok(false)
    }
}

// ═══════════════════════════════════════════════════════════════
// HELPER FUNCTIONS
// ═══════════════════════════════════════════════════════════════

fn get_vram_info() -> Result<(u64, u64, u64), String> {
    // Execute nvidia-smi
    let output = std::process::Command::new("nvidia-smi")
        .args(&["--query-gpu=memory.total,memory.used,memory.free", "--format=csv,noheader,nounits"])
        .output()
        .map_err(|e| format!("Failed to run nvidia-smi: {}", e))?;
    
    if !output.status.success() {
        return Err("nvidia-smi failed".to_string());
    }
    
    let stdout = String::from_utf8_lossy(&output.stdout);
    let values: Vec<&str> = stdout.trim().split(',').collect();
    
    if values.len() != 3 {
        return Err("Invalid nvidia-smi output".to_string());
    }
    
    let total = values[0].trim().parse::<u64>().unwrap_or(0);
    let used = values[1].trim().parse::<u64>().unwrap_or(0);
    let free = values[2].trim().parse::<u64>().unwrap_or(0);
    
    Ok((total, used, free))
}

fn get_config_path() -> std::path::PathBuf {
    let mut path = dirs::config_dir().unwrap_or_else(|| std::path::PathBuf::from("."));
    path.push("cortex-desktop");
    std::fs::create_dir_all(&path).ok();
    path.push("config.json");
    path
}

// ═══════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════

fn main() {
    // Default configuration
    let default_config = AppConfig {
        providers: vec![
            Provider {
                name: "Local".to_string(),
                provider_type: "local".to_string(),
                base_url: Some("http://localhost:8080".to_string()),
                model: "Qwen3-Coder-30B".to_string(),
                parameters: ModelParameters {
                    temperature: 0.7,
                    top_p: 0.9,
                    max_tokens: 2048,
                    context_size: 4096,
                },
            }
        ],
        active_provider: "Local".to_string(),
        api_keys: std::collections::HashMap::new(),
    };
    
    tauri::Builder::default()
        .manage(Mutex::new(default_config))
        .invoke_handler(tauri::generate_handler![
            process_document,
            semantic_search,
            rag_query,
            get_system_stats,
            save_config,
            load_config,
            health_check
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

// ═══════════════════════════════════════════════════════════════
// Cargo.toml DEPENDENCIES
// ═══════════════════════════════════════════════════════════════

/*
[package]
name = "cortex-desktop"
version = "2.0.0"
edition = "2021"

[dependencies]
tauri = { version = "1.5", features = ["shell-open", "dialog-all", "fs-all", "http-all"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
reqwest = { version = "0.11", features = ["json", "multipart"] }
tokio = { version = "1", features = ["full"] }
sysinfo = "0.30"
dirs = "5.0"

[features]
default = ["custom-protocol"]
custom-protocol = ["tauri/custom-protocol"]
*/

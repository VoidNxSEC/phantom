//! PhantomAgent - Real integration with Phantom engine
//! Implements Agent trait for document processing via Phantom

use anyhow::{Context as AnyhowContext, Result};
use std::path::PathBuf;
use std::process::Stdio;
use tokio::process::Command;
use tracing::{debug, error, info, warn};

/// Result from processing a document
#[derive(Debug, Clone)]
pub struct ProcessResult {
    pub success: bool,
    pub duration_ms: u64,
    pub stdout: String,
    pub stderr: String,
    pub output_dir: String,
}

pub struct PhantomAgent {
    /// Path to phantom executable
    phantom_bin: PathBuf,

    /// Agent ID
    id: String,

    /// Working directory
    work_dir: PathBuf,
}

impl PhantomAgent {
    pub fn new() -> Result<Self> {
        // Find phantom binary (should be in PATH via nix develop)
        let phantom_bin = which::which("phantom")
            .context("Phantom binary not found in PATH. Are you in nix develop?")?;

        info!("Found Phantom at: {:?}", phantom_bin);

        Ok(Self {
            phantom_bin,
            id: format!("phantom-{}", uuid::Uuid::new_v4()),
            work_dir: std::env::current_dir()?,
        })
    }

    /// Execute Phantom on a file
    pub async fn process_file(&self, input_path: PathBuf) -> Result<ProcessResult> {
        info!("PhantomAgent processing: {:?}", input_path);

        // Validate input exists
        if !input_path.exists() {
            return Err(anyhow::anyhow!(
                "Input file does not exist: {:?}",
                input_path
            ));
        }

        // Create output directory
        let output_dir = self.work_dir.join(".phantom/output");
        tokio::fs::create_dir_all(&output_dir).await?;

        debug!("Output directory: {:?}", output_dir);

        // Build Phantom command
        let mut cmd = Command::new(&self.phantom_bin);
        cmd.arg("-i")
            .arg(&input_path)
            .arg("-o")
            .arg(&output_dir)
            .arg("-v") // Verbose
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        debug!("Executing: {:?}", cmd);

        // Execute
        let start = std::time::Instant::now();
        let output = cmd.output().await.context("Failed to execute Phantom")?;
        let duration = start.elapsed();

        // Parse output
        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);

        debug!("Phantom stdout: {}", stdout);
        if !stderr.is_empty() {
            warn!("Phantom stderr: {}", stderr);
        }

        if !output.status.success() {
            error!("Phantom failed with exit code: {:?}", output.status.code());
            return Err(anyhow::anyhow!("Phantom execution failed: {}", stderr));
        }

        info!("Phantom completed in {:?}", duration);

        Ok(ProcessResult {
            success: true,
            duration_ms: duration.as_millis() as u64,
            stdout: stdout.to_string(),
            stderr: stderr.to_string(),
            output_dir: output_dir.to_string_lossy().to_string(),
        })
    }

    pub fn id(&self) -> &str {
        &self.id
    }
}

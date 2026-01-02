//! Task Queue - Observable MPSC-based task distribution
//!
//! Pure channel-based queue. No abstractions.
//! Every enqueue/dequeue is an event.

use anyhow::Result;
use std::path::PathBuf;
use tokio::sync::mpsc;
use tracing::{debug, info};

/// Task types that can be executed
#[derive(Debug, Clone)]
pub enum Task {
    ProcessDocument {
        id: u64,
        file_path: PathBuf,
    },
    // Future task types
    #[allow(dead_code)]
    Custom {
        id: u64,
        data: String,
    },
}

/// Task result after execution
#[derive(Debug, Clone)]
pub struct TaskResult {
    pub task_id: u64,
    pub success: bool,
    pub duration_ms: u64,
    pub output: String,
    pub error: Option<String>,
}

/// Observable task queue
pub struct TaskQueue {
    tx: mpsc::UnboundedSender<Task>,
    rx: mpsc::UnboundedReceiver<Task>,

    /// Stats (observable)
    pub total_enqueued: std::sync::atomic::AtomicU64,
    pub total_dequeued: std::sync::atomic::AtomicU64,
}

impl TaskQueue {
    pub fn new() -> Self {
        let (tx, rx) = mpsc::unbounded_channel();

        Self {
            tx,
            rx,
            total_enqueued: std::sync::atomic::AtomicU64::new(0),
            total_dequeued: std::sync::atomic::AtomicU64::new(0),
        }
    }

    /// Enqueue a task (observable)
    pub fn enqueue(&self, task: Task) -> Result<()> {
        debug!("QUEUE: Enqueuing task: {:?}", task);

        self.tx.send(task)
            .map_err(|e| anyhow::anyhow!("Failed to enqueue: {}", e))?;

        self.total_enqueued.fetch_add(1, std::sync::atomic::Ordering::Relaxed);

        info!("QUEUE: Total enqueued: {}", self.total_enqueued.load(std::sync::atomic::Ordering::Relaxed));

        Ok(())
    }

    /// Dequeue a task (blocking async, observable)
    pub async fn dequeue(&mut self) -> Option<Task> {
        match self.rx.recv().await {
            Some(task) => {
                debug!("QUEUE: Dequeued task: {:?}", task);
                self.total_dequeued.fetch_add(1, std::sync::atomic::Ordering::Relaxed);

                info!("QUEUE: Total dequeued: {}", self.total_dequeued.load(std::sync::atomic::Ordering::Relaxed));

                Some(task)
            }
            None => {
                debug!("QUEUE: Channel closed");
                None
            }
        }
    }

    /// Get queue depth (observable metric)
    pub fn depth(&self) -> u64 {
        let enqueued = self.total_enqueued.load(std::sync::atomic::Ordering::Relaxed);
        let dequeued = self.total_dequeued.load(std::sync::atomic::Ordering::Relaxed);
        enqueued.saturating_sub(dequeued)
    }

    /// Clone sender for multi-producer
    pub fn sender(&self) -> mpsc::UnboundedSender<Task> {
        self.tx.clone()
    }
}

impl Default for TaskQueue {
    fn default() -> Self {
        Self::new()
    }
}

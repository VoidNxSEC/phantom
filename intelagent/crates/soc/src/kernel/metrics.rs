//! Metrics Collector - Real-time performance telemetry
//!
//! Collect, aggregate, expose. No magic.

use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use tracing::debug;

/// System-wide metrics (observable, lock-free)
#[derive(Debug)]
pub struct Metrics {
    // Task metrics
    pub tasks_enqueued: Arc<AtomicU64>,
    pub tasks_completed: Arc<AtomicU64>,
    pub tasks_failed: Arc<AtomicU64>,

    // Timing metrics (in milliseconds)
    pub total_execution_time_ms: Arc<AtomicU64>,
    pub min_execution_time_ms: Arc<AtomicU64>,
    pub max_execution_time_ms: Arc<AtomicU64>,

    // Agent metrics
    pub agents_spawned: Arc<AtomicU64>,
    pub agents_active: Arc<AtomicU64>,
}

impl Metrics {
    pub fn new() -> Self {
        Self {
            tasks_enqueued: Arc::new(AtomicU64::new(0)),
            tasks_completed: Arc::new(AtomicU64::new(0)),
            tasks_failed: Arc::new(AtomicU64::new(0)),
            total_execution_time_ms: Arc::new(AtomicU64::new(0)),
            min_execution_time_ms: Arc::new(AtomicU64::new(u64::MAX)),
            max_execution_time_ms: Arc::new(AtomicU64::new(0)),
            agents_spawned: Arc::new(AtomicU64::new(0)),
            agents_active: Arc::new(AtomicU64::new(0)),
        }
    }

    /// Record task enqueued
    pub fn record_enqueue(&self) {
        self.tasks_enqueued.fetch_add(1, Ordering::Relaxed);
        debug!(
            "METRICS: Tasks enqueued: {}",
            self.tasks_enqueued.load(Ordering::Relaxed)
        );
    }

    /// Record task completed
    pub fn record_completion(&self, duration_ms: u64) {
        self.tasks_completed.fetch_add(1, Ordering::Relaxed);
        self.total_execution_time_ms
            .fetch_add(duration_ms, Ordering::Relaxed);

        // Update min
        self.min_execution_time_ms
            .fetch_min(duration_ms, Ordering::Relaxed);

        // Update max
        self.max_execution_time_ms
            .fetch_max(duration_ms, Ordering::Relaxed);

        debug!(
            "METRICS: Task completed in {}ms (total: {})",
            duration_ms,
            self.tasks_completed.load(Ordering::Relaxed)
        );
    }

    /// Record task failure
    pub fn record_failure(&self) {
        self.tasks_failed.fetch_add(1, Ordering::Relaxed);
        debug!(
            "METRICS: Task failed (total failures: {})",
            self.tasks_failed.load(Ordering::Relaxed)
        );
    }

    /// Get snapshot (observable state)
    pub fn snapshot(&self) -> MetricsSnapshot {
        let enqueued = self.tasks_enqueued.load(Ordering::Relaxed);
        let completed = self.tasks_completed.load(Ordering::Relaxed);
        let failed = self.tasks_failed.load(Ordering::Relaxed);
        let total_time = self.total_execution_time_ms.load(Ordering::Relaxed);
        let min_time = self.min_execution_time_ms.load(Ordering::Relaxed);
        let max_time = self.max_execution_time_ms.load(Ordering::Relaxed);

        let avg_time = if completed > 0 {
            total_time / completed
        } else {
            0
        };

        MetricsSnapshot {
            tasks_enqueued: enqueued,
            tasks_completed: completed,
            tasks_failed: failed,
            tasks_in_progress: enqueued.saturating_sub(completed + failed),
            avg_execution_time_ms: avg_time,
            min_execution_time_ms: if min_time == u64::MAX { 0 } else { min_time },
            max_execution_time_ms: max_time,
            success_rate: if completed + failed > 0 {
                (completed as f64 / (completed + failed) as f64) * 100.0
            } else {
                0.0
            },
        }
    }
}

impl Default for Metrics {
    fn default() -> Self {
        Self::new()
    }
}

/// Metrics snapshot (immutable view)
#[derive(Debug, Clone)]
pub struct MetricsSnapshot {
    pub tasks_enqueued: u64,
    pub tasks_completed: u64,
    pub tasks_failed: u64,
    pub tasks_in_progress: u64,
    pub avg_execution_time_ms: u64,
    pub min_execution_time_ms: u64,
    pub max_execution_time_ms: u64,
    pub success_rate: f64,
}

/// Metrics collector (thin wrapper for dependency injection)
pub struct MetricsCollector {
    metrics: Arc<Metrics>,
}

impl MetricsCollector {
    pub fn new(metrics: Arc<Metrics>) -> Self {
        Self { metrics }
    }

    pub fn metrics(&self) -> &Metrics {
        &self.metrics
    }
}

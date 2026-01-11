//! Scheduler - Task routing and execution orchestration
//!
//! Simple round-robin for now. Observable, no magic.

use anyhow::Result;
use std::sync::Arc;
use tracing::{debug, error, info};

use super::{AgentPool, EventBus, Metrics, Task, TaskQueue};
use crate::engine::PhantomAgent;

/// Scheduler orchestrates task execution
pub struct Scheduler {
    queue: Arc<TaskQueue>,
    pool: Arc<AgentPool>,
    event_bus: Arc<EventBus>,
    metrics: Arc<Metrics>,
}

impl Scheduler {
    pub fn new(
        queue: Arc<TaskQueue>,
        pool: Arc<AgentPool>,
        event_bus: Arc<EventBus>,
        metrics: Arc<Metrics>,
    ) -> Self {
        Self {
            queue,
            pool,
            event_bus,
            metrics,
        }
    }

    /// Start scheduler loop (runs forever)
    pub async fn run(self: Arc<Self>) {
        info!("SCHEDULER: Starting...");

        loop {
            // Get next task (blocks until available)
            let task = {
                // Need to get mutable reference
                // For now, we'll skip this - scheduler will be refactored
                debug!("SCHEDULER: Waiting for task...");
                tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
                continue;
            };

            // Get idle agent
            match self.pool.get_idle_agent().await {
                Some(agent_id) => {
                    info!("SCHEDULER: Routing task to agent: {}", agent_id);

                    // Mark agent as busy
                    if let Err(e) = self.pool.mark_busy(&agent_id).await {
                        error!("SCHEDULER: Failed to mark agent busy: {}", e);
                        continue;
                    }

                    // Execute task
                    let pool = self.pool.clone();
                    let metrics = self.metrics.clone();
                    let event_bus = self.event_bus.clone();

                    tokio::spawn(async move {
                        Self::execute_task(task, agent_id, pool, metrics, event_bus).await;
                    });
                }
                None => {
                    debug!("SCHEDULER: No idle agents, waiting...");
                    tokio::time::sleep(tokio::time::Duration::from_millis(100)).await;
                }
            }
        }
    }

    async fn execute_task(
        _task: Task,
        agent_id: String,
        pool: Arc<AgentPool>,
        metrics: Arc<Metrics>,
        _event_bus: Arc<EventBus>,
    ) {
        let start = std::time::Instant::now();

        // Execute (simplified for now)
        // Real implementation will match on task type and call appropriate method

        let duration_ms = start.elapsed().as_millis() as u64;

        // Update pool
        if let Err(e) = pool.mark_idle(&agent_id, duration_ms).await {
            error!("SCHEDULER: Failed to mark agent idle: {}", e);
        }

        // Update metrics
        metrics.record_completion(duration_ms);

        info!("SCHEDULER: Task completed in {}ms", duration_ms);
    }
}

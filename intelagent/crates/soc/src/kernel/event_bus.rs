//! Event Bus - Full telemetry stream
//!
//! EVERY action in the system emits an event.
//! UI subscribes to this stream for real-time observability.

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use tokio::sync::broadcast;
use tracing::debug;

/// All possible events in the system
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Event {
    /// Task lifecycle
    TaskEnqueued {
        id: u64,
        timestamp: DateTime<Utc>,
    },
    TaskDequeued {
        id: u64,
        timestamp: DateTime<Utc>,
    },
    TaskStarted {
        id: u64,
        agent_id: String,
        timestamp: DateTime<Utc>,
    },
    TaskCompleted {
        id: u64,
        duration_ms: u64,
        timestamp: DateTime<Utc>,
    },
    TaskFailed {
        id: u64,
        error: String,
        timestamp: DateTime<Utc>,
    },

    /// Agent lifecycle
    AgentSpawned {
        id: String,
        timestamp: DateTime<Utc>,
    },
    AgentIdle {
        id: String,
        timestamp: DateTime<Utc>,
    },
    AgentBusy {
        id: String,
        timestamp: DateTime<Utc>,
    },
    AgentKilled {
        id: String,
        timestamp: DateTime<Utc>,
    },

    /// System events
    MetricsSnapshot {
        queue_depth: u64,
        active_agents: usize,
        total_processed: u64,
        timestamp: DateTime<Utc>,
    },
}

/// Event bus for system-wide telemetry
pub struct EventBus {
    tx: broadcast::Sender<Event>,
}

impl EventBus {
    pub fn new(capacity: usize) -> Self {
        let (tx, _) = broadcast::channel(capacity);
        Self { tx }
    }

    /// Emit an event (observable)
    pub fn emit(&self, event: Event) {
        debug!("EVENT: {:?}", event);

        // Send to all subscribers
        // If no subscribers, message is dropped (that's ok)
        let _ = self.tx.send(event);
    }

    /// Subscribe to events
    pub fn subscribe(&self) -> broadcast::Receiver<Event> {
        self.tx.subscribe()
    }

    /// Get subscriber count (observable)
    pub fn subscriber_count(&self) -> usize {
        self.tx.receiver_count()
    }
}

impl Default for EventBus {
    fn default() -> Self {
        Self::new(1000) // Buffer 1000 events
    }
}

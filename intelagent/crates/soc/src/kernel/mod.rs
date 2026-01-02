//! Orchestration Kernel - Pure, observable, no abstractions
//!
//! This is the core of IntelAgent SOC. Everything here is:
//! - Observable (all state changes logged)
//! - Measurable (all metrics collected)
//! - Controllable (direct access to internals)
//!
//! NO MAGIC. NO ABSTRACTIONS. KERNEL MODE.

pub mod agent_pool;
pub mod event_bus;
pub mod metrics;
pub mod scheduler;
pub mod task_queue;

pub use agent_pool::{AgentMetadata, AgentPool, AgentState, PoolStats};
pub use event_bus::{Event, EventBus};
pub use metrics::{Metrics, MetricsCollector, MetricsSnapshot};
pub use scheduler::Scheduler;
pub use task_queue::{Task, TaskQueue, TaskResult};

//! Agent abstraction and core types

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use std::fmt;
use uuid::Uuid;

use crate::{Context, Reputation, Task, TaskResult};

/// Unique identifier for an agent
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct AgentId(Uuid);

impl AgentId {
    /// Generate new random agent ID
    pub fn new() -> Self {
        AgentId(Uuid::new_v4())
    }

    /// Create from existing UUID
    pub fn from_uuid(uuid: Uuid) -> Self {
        AgentId(uuid)
    }

    /// Get inner UUID
    pub fn as_uuid(&self) -> &Uuid {
        &self.0
    }
}

impl Default for AgentId {
    fn default() -> Self {
        Self::new()
    }
}

impl fmt::Display for AgentId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// Agent capability assessment for a task
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Capability {
    /// Can this agent handle the task?
    pub can_handle: bool,

    /// Confidence level (0.0 to 1.0)
    pub confidence: f64,

    /// Estimated effort (arbitrary units)
    pub estimated_effort: f64,

    /// Reasoning for capability assessment
    pub reasoning: String,
}

impl Capability {
    /// Agent cannot handle this task
    pub fn cannot_handle(reason: impl Into<String>) -> Self {
        Capability {
            can_handle: false,
            confidence: 0.0,
            estimated_effort: 0.0,
            reasoning: reason.into(),
        }
    }

    /// Agent can handle with given confidence
    pub fn can_handle(confidence: f64, effort: f64, reasoning: impl Into<String>) -> Self {
        Capability {
            can_handle: true,
            confidence,
            estimated_effort: effort,
            reasoning: reasoning.into(),
        }
    }
}

/// Agent metadata (name, description, specialization)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentMetadata {
    pub name: String,
    pub description: String,
    pub version: String,
    pub specialization: Vec<String>,
}

/// Core Agent trait - all agents must implement this
#[async_trait]
pub trait Agent: Send + Sync {
    /// Execute a task with full context
    ///
    /// This is the primary method agents implement. It receives:
    /// - `task`: The work to be done
    /// - `context`: Shared knowledge (project memory, MCP servers, DAO state)
    ///
    /// Returns:
    /// - `TaskResult`: Output, quality metrics, proof of correctness
    async fn execute(&self, task: Task, context: &Context) -> anyhow::Result<TaskResult>;

    /// Self-assessment of capability for given task
    ///
    /// Agents should honestly assess if they can handle a task.
    /// This enables intelligent task routing.
    fn can_handle(&self, task: &Task) -> Capability;

    /// Unique identifier (cryptographically signed in production)
    fn id(&self) -> AgentId;

    /// Agent metadata (name, description, etc)
    fn metadata(&self) -> AgentMetadata;

    /// Current reputation score (from DAO)
    ///
    /// In production, this queries the blockchain.
    /// In development, uses local cache.
    async fn reputation(&self) -> Reputation {
        // Default implementation - override with DAO integration
        Reputation::default_new_agent()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_agent_id_generation() {
        let id1 = AgentId::new();
        let id2 = AgentId::new();
        assert_ne!(id1, id2);
    }

    #[test]
    fn test_capability_cannot_handle() {
        let cap = Capability::cannot_handle("Task requires GPU");
        assert!(!cap.can_handle);
        assert_eq!(cap.confidence, 0.0);
    }

    #[test]
    fn test_capability_can_handle() {
        let cap = Capability::can_handle(0.9, 5.0, "Expert in this domain");
        assert!(cap.can_handle);
        assert_eq!(cap.confidence, 0.9);
        assert_eq!(cap.estimated_effort, 5.0);
    }
}

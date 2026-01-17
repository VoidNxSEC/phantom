//! Task abstraction and related types

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fmt;
use uuid::Uuid;

use crate::{ContextQuery, Proof, QualityGate};

/// Unique identifier for a task
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct TaskId(Uuid);

impl TaskId {
    pub fn new() -> Self {
        TaskId(Uuid::new_v4())
    }

    pub fn from_uuid(uuid: Uuid) -> Self {
        TaskId(uuid)
    }

    pub fn as_uuid(&self) -> &Uuid {
        &self.0
    }
}

impl Default for TaskId {
    fn default() -> Self {
        Self::new()
    }
}

impl fmt::Display for TaskId {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// Task requirements (functional)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Requirements {
    /// What must be accomplished
    pub objectives: Vec<String>,

    /// Expected output format
    pub output_format: OutputFormat,

    /// Minimum quality threshold
    pub min_quality_score: f64,
}

/// Expected output format
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OutputFormat {
    Json,
    Text,
    Code { language: String },
    Binary,
    Custom(String),
}

/// Task constraints (non-functional)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Constraints {
    /// Maximum execution time
    pub max_duration: Option<std::time::Duration>,

    /// Maximum resource usage
    pub max_tokens: Option<usize>,

    /// Privacy level required
    pub privacy_level: PrivacyLevel,

    /// Must use specific models
    pub required_models: Vec<String>,
}

/// Privacy level for task execution
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PrivacyLevel {
    /// No privacy needed, full transparency
    Public,

    /// ZK proofs required, data encrypted
    Private,

    /// TEE required, no external communication
    Confidential,

    /// Air-gapped execution, manual verification
    TopSecret,
}

/// Task status
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum TaskStatus {
    Pending,
    Assigned,
    InProgress,
    UnderReview,
    Completed,
    Failed,
    Rejected,
}

/// A unit of work with requirements and constraints
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Task {
    pub id: TaskId,
    pub description: String,
    pub input: TaskInput,
    pub requirements: Requirements,
    pub constraints: Constraints,

    /// Context needed from MCP servers
    pub context_needed: Vec<ContextQuery>,

    /// Quality gates that must pass
    #[serde(skip)]
    pub quality_gates: Vec<Box<dyn QualityGate>>,

    /// Optional deadline
    pub deadline: Option<DateTime<Utc>>,

    /// Task metadata
    pub metadata: HashMap<String, String>,
}

/// Task input data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaskInput {
    Text(String),
    Json(serde_json::Value),
    Binary(Vec<u8>),
    FilePath(String),
}

impl Task {
    /// Create new task with minimal info
    pub fn new(description: impl Into<String>, input: TaskInput) -> Self {
        Task {
            id: TaskId::new(),
            description: description.into(),
            input,
            requirements: Requirements {
                objectives: vec![],
                output_format: OutputFormat::Text,
                min_quality_score: 0.8,
            },
            constraints: Constraints {
                max_duration: None,
                max_tokens: None,
                privacy_level: PrivacyLevel::Public,
                required_models: vec![],
            },
            context_needed: vec![],
            quality_gates: Vec::new(),
            deadline: None,
            metadata: HashMap::new(),
        }
    }

    /// Builder method: Add objective
    pub fn with_objective(mut self, objective: impl Into<String>) -> Self {
        self.requirements.objectives.push(objective.into());
        self
    }

    /// Builder method: Set privacy level
    pub fn with_privacy(mut self, level: PrivacyLevel) -> Self {
        self.constraints.privacy_level = level;
        self
    }

    /// Builder method: Add quality gate
    pub fn with_quality_gate(mut self, gate: Box<dyn QualityGate>) -> Self {
        self.quality_gates.push(gate);
        self
    }
}

/// Result of task execution
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskResult {
    pub task_id: TaskId,
    pub output: TaskOutput,
    pub quality_score: f64,
    pub execution_time_ms: u64,

    /// Optional ZK proof of correctness
    pub proof: Option<Proof>,

    /// Evidence of validation (tests run, etc)
    pub validation_evidence: Vec<String>,

    /// Agent's summary of work done
    pub summary: String,

    /// Metadata
    pub metadata: HashMap<String, String>,
}

/// Task output data
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TaskOutput {
    Text(String),
    Json(serde_json::Value),
    Binary(Vec<u8>),
    Error(String),
}

impl TaskResult {
    /// Create successful result
    pub fn success(
        task_id: TaskId,
        output: TaskOutput,
        quality_score: f64,
        execution_time_ms: u64,
    ) -> Self {
        TaskResult {
            task_id,
            output,
            quality_score,
            execution_time_ms,
            proof: None,
            validation_evidence: vec![],
            summary: String::new(),
            metadata: HashMap::new(),
        }
    }

    /// Create error result
    pub fn error(task_id: TaskId, error: impl Into<String>) -> Self {
        TaskResult {
            task_id,
            output: TaskOutput::Error(error.into()),
            quality_score: 0.0,
            execution_time_ms: 0,
            proof: None,
            validation_evidence: vec![],
            summary: String::new(),
            metadata: HashMap::new(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_task_builder() {
        let task = Task::new("Test task", TaskInput::Text("input".to_string()))
            .with_objective("Objective 1")
            .with_objective("Objective 2")
            .with_privacy(PrivacyLevel::Private);

        assert_eq!(task.requirements.objectives.len(), 2);
        assert_eq!(task.constraints.privacy_level, PrivacyLevel::Private);
    }

    #[test]
    fn test_task_result_success() {
        let task_id = TaskId::new();
        let result = TaskResult::success(task_id, TaskOutput::Text("done".to_string()), 0.95, 1000);

        assert_eq!(result.task_id, task_id);
        assert_eq!(result.quality_score, 0.95);
    }
}

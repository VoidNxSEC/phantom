//! Quality gates and validation

use async_trait::async_trait;
use serde::{Deserialize, Serialize};

use crate::TaskResult;

/// Severity level of quality gate
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Severity {
    /// Must pass - blocks completion
    Critical,

    /// Should pass - generates warning
    Warning,

    /// Nice to have - informational
    Info,
}

/// Result of validation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationResult {
    pub check_name: String,
    pub passed: bool,
    pub severity: Severity,
    pub message: String,
    pub evidence: Option<String>,
}

impl ValidationResult {
    pub fn passed(name: impl Into<String>, message: impl Into<String>) -> Self {
        ValidationResult {
            check_name: name.into(),
            passed: true,
            severity: Severity::Info,
            message: message.into(),
            evidence: None,
        }
    }

    pub fn failed(name: impl Into<String>, severity: Severity, message: impl Into<String>) -> Self {
        ValidationResult {
            check_name: name.into(),
            passed: false,
            severity,
            message: message.into(),
            evidence: None,
        }
    }

    pub fn with_evidence(mut self, evidence: impl Into<String>) -> Self {
        self.evidence = Some(evidence.into());
        self
    }
}

/// Objective validation that must pass before task completion
#[async_trait]
pub trait QualityGate: Send + Sync + std::fmt::Debug {
    /// Validate task result
    async fn validate(&self, result: &TaskResult) -> ValidationResult;

    /// Severity (CRITICAL gates block completion)
    fn severity(&self) -> Severity;

    /// Human-readable description
    fn description(&self) -> String;

    /// Unique identifier for this gate
    fn id(&self) -> String;

    /// Clone support for trait objects
    fn clone_box(&self) -> Box<dyn QualityGate>;
}

impl Clone for Box<dyn QualityGate> {
    fn clone(&self) -> Box<dyn QualityGate> {
        self.clone_box()
    }
}

/// Built-in quality gate: Minimum quality score
#[derive(Debug, Clone)]
pub struct MinQualityScoreGate {
    pub threshold: f64,
}

#[async_trait]
impl QualityGate for MinQualityScoreGate {
    async fn validate(&self, result: &TaskResult) -> ValidationResult {
        if result.quality_score >= self.threshold {
            ValidationResult::passed(
                "min_quality_score",
                format!(
                    "Quality score {} meets threshold {}",
                    result.quality_score, self.threshold
                ),
            )
        } else {
            ValidationResult::failed(
                "min_quality_score",
                Severity::Critical,
                format!(
                    "Quality score {} below threshold {}",
                    result.quality_score, self.threshold
                ),
            )
        }
    }

    fn severity(&self) -> Severity {
        Severity::Critical
    }

    fn description(&self) -> String {
        format!("Quality score must be >= {}", self.threshold)
    }

    fn id(&self) -> String {
        "min_quality_score".to_string()
    }

    fn clone_box(&self) -> Box<dyn QualityGate> {
        Box::new(self.clone())
    }
}

/// Built-in quality gate: Must provide validation evidence
#[derive(Debug, Clone)]
pub struct ValidationEvidenceGate;

#[async_trait]
impl QualityGate for ValidationEvidenceGate {
    async fn validate(&self, result: &TaskResult) -> ValidationResult {
        if !result.validation_evidence.is_empty() {
            ValidationResult::passed(
                "validation_evidence",
                format!(
                    "Provided {} pieces of evidence",
                    result.validation_evidence.len()
                ),
            )
            .with_evidence(result.validation_evidence.join("\n"))
        } else {
            ValidationResult::failed(
                "validation_evidence",
                Severity::Critical,
                "No validation evidence provided (tests, checks, etc)",
            )
        }
    }

    fn severity(&self) -> Severity {
        Severity::Critical
    }

    fn description(&self) -> String {
        "Must provide evidence of validation (tests run, checks passed, etc)".to_string()
    }

    fn id(&self) -> String {
        "validation_evidence".to_string()
    }

    fn clone_box(&self) -> Box<dyn QualityGate> {
        Box::new(self.clone())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::{TaskId, TaskOutput};

    #[tokio::test]
    async fn test_min_quality_score_gate_pass() {
        let gate = MinQualityScoreGate { threshold: 0.8 };
        let result = TaskResult::success(
            TaskId::new(),
            TaskOutput::Text("done".to_string()),
            0.9,
            1000,
        );

        let validation = gate.validate(&result).await;
        assert!(validation.passed);
    }

    #[tokio::test]
    async fn test_min_quality_score_gate_fail() {
        let gate = MinQualityScoreGate { threshold: 0.8 };
        let result = TaskResult::success(
            TaskId::new(),
            TaskOutput::Text("done".to_string()),
            0.7,
            1000,
        );

        let validation = gate.validate(&result).await;
        assert!(!validation.passed);
        assert_eq!(validation.severity, Severity::Critical);
    }
}

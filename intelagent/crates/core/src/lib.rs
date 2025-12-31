//! # IntelAgent Core
//!
//! Core abstractions for intelligent agent orchestration.
//!
//! This crate defines the fundamental traits and types that all IntelAgent
//! components build upon:
//!
//! - [`Agent`] - Autonomous units of work
//! - [`Task`] - Units of work with requirements
//! - [`QualityGate`] - Objective validation
//! - [`Context`] - Shared knowledge
//! - [`Proof`] - Zero-knowledge proofs

pub mod agent;
pub mod context;
pub mod proof;
pub mod quality;
pub mod task;
pub mod types;

// Re-exports
pub use agent::{Agent, AgentId, AgentMetadata, Capability};
pub use context::{Context, ContextQuery, ProjectMemory};
pub use proof::{Proof, ProofType, VerificationResult};
pub use quality::{QualityGate, Severity, ValidationResult};
pub use task::{Constraints, Requirements, Task, TaskId, TaskResult, TaskStatus};
pub use types::{Reputation, Timestamp};

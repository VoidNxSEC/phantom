//! Shared context and knowledge

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// Query for context from MCP servers
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContextQuery {
    /// Which MCP server to query
    pub server: String,

    /// Method to call
    pub method: String,

    /// Parameters
    pub params: HashMap<String, serde_json::Value>,
}

/// Project memory - architecture decisions, conventions, standards
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectMemory {
    /// Architecture Decision Records
    pub adrs: Vec<ArchitectureDecision>,

    /// Code conventions
    pub conventions: Conventions,

    /// Quality standards
    pub quality_standards: QualityStandards,

    /// Known issues
    pub known_issues: Vec<String>,
}

/// Architecture Decision Record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArchitectureDecision {
    pub id: String,
    pub title: String,
    pub decision: String,
    pub rationale: String,
    pub date: String,
    pub impact: String,
    pub status: ADRStatus,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ADRStatus {
    Proposed,
    Accepted,
    Deprecated,
    Superseded,
}

/// Code conventions
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Conventions {
    pub code_style: Vec<String>,
    pub file_organization: Vec<String>,
    pub naming: Vec<String>,
    pub testing: Vec<String>,
}

/// Quality standards
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QualityStandards {
    pub code: Vec<String>,
    pub testing: Vec<String>,
    pub documentation: Vec<String>,
    pub performance: Vec<String>,
}

/// Shared knowledge available to agents
#[derive(Debug, Clone)]
pub struct Context {
    pub project_memory: ProjectMemory,
    // TODO: Add MCP servers, DAO state, audit trail
}

impl Context {
    /// Create new empty context
    pub fn new() -> Self {
        Context {
            project_memory: ProjectMemory {
                adrs: vec![],
                conventions: Conventions {
                    code_style: vec![],
                    file_organization: vec![],
                    naming: vec![],
                    testing: vec![],
                },
                quality_standards: QualityStandards {
                    code: vec![],
                    testing: vec![],
                    documentation: vec![],
                    performance: vec![],
                },
                known_issues: vec![],
            },
        }
    }

    /// Load from file (YAML or JSON)
    pub fn load_from_file(_path: &str) -> anyhow::Result<Self> {
        // TODO: Implement file loading
        Ok(Context::new())
    }
}

impl Default for Context {
    fn default() -> Self {
        Self::new()
    }
}

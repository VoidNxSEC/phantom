//! Agent Pool - Lifecycle management with full observability
//!
//! Spawn, monitor, kill agents. All state visible.

use anyhow::Result;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{debug, info, warn};

use crate::engine::PhantomAgent;

/// Agent state (observable)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AgentState {
    Idle,
    Busy,
    Failed,
}

/// Agent metadata (observable)
#[derive(Debug, Clone)]
pub struct AgentMetadata {
    pub id: String,
    pub state: AgentState,
    pub tasks_completed: u64,
    pub total_duration_ms: u64,
}

/// Pool of Phantom agents with full lifecycle control
pub struct AgentPool {
    agents: Arc<RwLock<HashMap<String, AgentMetadata>>>,
    max_agents: usize,
}

impl AgentPool {
    pub fn new(max_agents: usize) -> Self {
        info!("POOL: Creating agent pool (max: {})", max_agents);

        Self {
            agents: Arc::new(RwLock::new(HashMap::new())),
            max_agents,
        }
    }

    /// Spawn a new agent (observable)
    pub async fn spawn(&self) -> Result<String> {
        let mut agents = self.agents.write().await;

        if agents.len() >= self.max_agents {
            warn!("POOL: Max agents reached ({})", self.max_agents);
            return Err(anyhow::anyhow!("Agent pool full"));
        }

        let agent = PhantomAgent::new()?;
        let id = agent.id().to_string();

        let metadata = AgentMetadata {
            id: id.clone(),
            state: AgentState::Idle,
            tasks_completed: 0,
            total_duration_ms: 0,
        };

        agents.insert(id.clone(), metadata);

        info!("POOL: Spawned agent: {} (total: {})", id, agents.len());

        Ok(id)
    }

    /// Mark agent as busy (observable state transition)
    pub async fn mark_busy(&self, agent_id: &str) -> Result<()> {
        let mut agents = self.agents.write().await;

        if let Some(meta) = agents.get_mut(agent_id) {
            debug!("POOL: Agent {} -> BUSY", agent_id);
            meta.state = AgentState::Busy;
            Ok(())
        } else {
            Err(anyhow::anyhow!("Agent not found: {}", agent_id))
        }
    }

    /// Mark agent as idle (observable state transition)
    pub async fn mark_idle(&self, agent_id: &str, duration_ms: u64) -> Result<()> {
        let mut agents = self.agents.write().await;

        if let Some(meta) = agents.get_mut(agent_id) {
            debug!("POOL: Agent {} -> IDLE (completed in {}ms)", agent_id, duration_ms);
            meta.state = AgentState::Idle;
            meta.tasks_completed += 1;
            meta.total_duration_ms += duration_ms;
            Ok(())
        } else {
            Err(anyhow::anyhow!("Agent not found: {}", agent_id))
        }
    }

    /// Get idle agent (observable)
    pub async fn get_idle_agent(&self) -> Option<String> {
        let agents = self.agents.read().await;

        agents.iter()
            .find(|(_, meta)| meta.state == AgentState::Idle)
            .map(|(id, _)| id.clone())
    }

    /// Get all agents (observable snapshot)
    pub async fn get_all(&self) -> Vec<AgentMetadata> {
        let agents = self.agents.read().await;
        agents.values().cloned().collect()
    }

    /// Get pool stats (observable metrics)
    pub async fn stats(&self) -> PoolStats {
        let agents = self.agents.read().await;

        let total = agents.len();
        let idle = agents.values().filter(|a| a.state == AgentState::Idle).count();
        let busy = agents.values().filter(|a| a.state == AgentState::Busy).count();
        let failed = agents.values().filter(|a| a.state == AgentState::Failed).count();

        PoolStats {
            total,
            idle,
            busy,
            failed,
        }
    }
}

/// Pool statistics (observable)
#[derive(Debug, Clone)]
pub struct PoolStats {
    pub total: usize,
    pub idle: usize,
    pub busy: usize,
    pub failed: usize,
}

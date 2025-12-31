//! Basic example of creating and running an agent

use intelagent_core::{
    Agent, AgentId, AgentMetadata, Capability, Context, Task, TaskInput, TaskOutput, TaskResult,
};

/// Simple agent that echoes input
struct EchoAgent {
    id: AgentId,
}

impl EchoAgent {
    fn new() -> Self {
        EchoAgent { id: AgentId::new() }
    }
}

#[async_trait::async_trait]
impl Agent for EchoAgent {
    async fn execute(&self, task: Task, _context: &Context) -> anyhow::Result<TaskResult> {
        let start = std::time::Instant::now();

        // Extract input
        let input_text = match task.input {
            TaskInput::Text(ref text) => text.clone(),
            _ => return Err(anyhow::anyhow!("EchoAgent only handles text input")),
        };

        // Simple processing - echo with prefix
        let output = format!("Echo: {}", input_text);

        // Create result
        let elapsed = start.elapsed();
        let mut result = TaskResult::success(
            task.id,
            TaskOutput::Text(output),
            0.95, // High quality for simple task
            elapsed.as_millis() as u64,
        );

        // Add evidence
        result.validation_evidence.push(format!("Processed {} bytes", input_text.len()));
        result.summary = "Successfully echoed input".to_string();

        Ok(result)
    }

    fn can_handle(&self, task: &Task) -> Capability {
        // Can only handle text input
        match task.input {
            TaskInput::Text(_) => Capability::can_handle(
                0.99,
                1.0, // Very low effort
                "Echo agent specializes in text tasks",
            ),
            _ => Capability::cannot_handle("Echo agent only handles text input"),
        }
    }

    fn id(&self) -> AgentId {
        self.id
    }

    fn metadata(&self) -> AgentMetadata {
        AgentMetadata {
            name: "EchoAgent".to_string(),
            description: "Simple agent that echoes input".to_string(),
            version: "0.1.0".to_string(),
            specialization: vec!["text".to_string(), "echo".to_string()],
        }
    }
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Create agent
    let agent = EchoAgent::new();

    // Create task
    let task = Task::new(
        "Echo this message",
        TaskInput::Text("Hello, IntelAgent!".to_string()),
    );

    // Check if agent can handle
    let capability = agent.can_handle(&task);
    println!("Can handle: {}", capability.can_handle);
    println!("Confidence: {}", capability.confidence);
    println!("Reasoning: {}", capability.reasoning);

    // Execute if capable
    if capability.can_handle {
        let context = Context::default();
        let result = agent.execute(task, &context).await?;

        println!("\n✅ Task completed!");
        println!("Quality score: {}", result.quality_score);
        println!("Execution time: {}ms", result.execution_time_ms);
        println!("Summary: {}", result.summary);

        if let TaskOutput::Text(output) = result.output {
            println!("Output: {}", output);
        }
    }

    Ok(())
}

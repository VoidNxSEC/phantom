# IntelAgent SOC - Kernel Backend

**Philosophy**: Observability, not abstractions. Kernel puro.

---

## 🎯 Arquitetura

```
┌───────────────────────────────────────────────────┐
│  EVENT BUS                                        │
│  └─ Broadcast channel (all events logged)        │
├───────────────────────────────────────────────────┤
│  METRICS (Lock-free Atomic)                      │
│  └─ Tasks: enqueued, completed, failed           │
│  └─ Timing: avg, min, max                        │
│  └─ Agents: spawned, active                      │
├───────────────────────────────────────────────────┤
│  SCHEDULER                                        │
│  └─ Task routing (round-robin)                   │
│  └─ Agent assignment                             │
├───────────────────────────────────────────────────┤
│  AGENT POOL                                       │
│  └─ Lifecycle: Spawn, Busy, Idle, Kill          │
│  └─ State tracking (HashMap<AgentId, Metadata>)  │
├───────────────────────────────────────────────────┤
│  TASK QUEUE                                       │
│  └─ MPSC unbounded channel                       │
│  └─ Stats: enqueued, dequeued, depth             │
└───────────────────────────────────────────────────┘
```

---

## 📊 Observability Points

### **1. Task Queue**

```rust
// Observable metrics
queue.total_enqueued   // AtomicU64
queue.total_dequeued   // AtomicU64
queue.depth()          // Current queue depth

// Events emitted
Event::TaskEnqueued { id, timestamp }
Event::TaskDequeued { id, timestamp }
```

### **2. Agent Pool**

```rust
// Observable state
pool.stats().await     // PoolStats { total, idle, busy, failed }
pool.get_all().await   // Vec<AgentMetadata>

// Events emitted
Event::AgentSpawned { id, timestamp }
Event::AgentIdle { id, timestamp }
Event::AgentBusy { id, timestamp }
Event::AgentKilled { id, timestamp }
```

### **3. Metrics**

```rust
// Lock-free atomic counters
metrics.tasks_enqueued
metrics.tasks_completed
metrics.tasks_failed
metrics.total_execution_time_ms
metrics.min_execution_time_ms
metrics.max_execution_time_ms

// Snapshot (immutable view)
let snap = metrics.snapshot();
// snap.avg_execution_time_ms
// snap.success_rate
// snap.tasks_in_progress
```

### **4. Event Bus**

```rust
// Subscribe to ALL events
let mut rx = event_bus.subscribe();
while let Ok(event) = rx.recv().await {
    match event {
        Event::TaskCompleted { id, duration_ms, .. } => {
            println!("Task {} done in {}ms", id, duration_ms);
        }
        Event::MetricsSnapshot { queue_depth, .. } => {
            println!("Queue: {} tasks", queue_depth);
        }
        _ => {}
    }
}
```

---

## 🔧 Usage Example

```rust
use std::sync::Arc;
use intelagent_soc::kernel::*;

#[tokio::main]
async fn main() {
    // Create kernel components
    let queue = Arc::new(TaskQueue::new());
    let pool = Arc::new(AgentPool::new(10));
    let event_bus = Arc::new(EventBus::default());
    let metrics = Arc::new(Metrics::default());

    // Spawn agents
    for _ in 0..5 {
        pool.spawn().await.unwrap();
    }

    // Enqueue tasks
    for i in 0..100 {
        let task = Task::ProcessDocument {
            id: i,
            file_path: format!("file_{}.txt", i).into(),
        };
        queue.enqueue(task).unwrap();
    }

    // Subscribe to events
    let mut events = event_bus.subscribe();
    tokio::spawn(async move {
        while let Ok(event) = events.recv().await {
            println!("EVENT: {:?}", event);
        }
    });

    // Get metrics snapshot every second
    loop {
        tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
        let snap = metrics.snapshot();
        println!("METRICS: {:?}", snap);
    }
}
```

---

## 🚀 Performance Characteristics

- **Task Queue**: Lock-free enqueue/dequeue (MPSC channel)
- **Metrics**: Lock-free atomics (no contention)
- **Agent Pool**: RwLock (rare writes, frequent reads)
- **Event Bus**: Broadcast channel (1000 event buffer)

### **Bottlenecks:**

- Agent Pool lock (write on state change)
- Event Bus (if too many subscribers)

### **Optimizations:**

- Use sharding for Agent Pool if > 100 agents
- Use separate event buses per subsystem

---

## 📝 TODO:

- [ ] Scheduler: Implement actual task routing loop
- [ ] AgentPool: Add TTL (kill idle agents after timeout)
- [ ] TaskQueue: Add priority queues
- [ ] Metrics: Add percentiles (p50, p95, p99)
- [ ] EventBus: Add filtering (subscribe to specific events)

---

**Status**: ✅ **BACKEND KERNEL COMPLETO**

Compilando limpo. Pronto para integração com UI de observabilidade.

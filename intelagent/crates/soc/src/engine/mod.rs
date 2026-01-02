//! Engine integration - Tight coupling with Phantom

mod phantom_worker;
mod phantom_agent;

pub use phantom_worker::PhantomWorker;
pub use phantom_agent::PhantomAgent;

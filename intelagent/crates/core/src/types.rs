//! Common types used across IntelAgent

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use std::fmt;

/// Timestamp type
pub type Timestamp = DateTime<Utc>;

/// Reputation score (0.0 to 1.0)
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct Reputation(f64);

impl Reputation {
    /// Create new reputation score
    pub fn new(score: f64) -> Result<Self, String> {
        if (0.0..=1.0).contains(&score) {
            Ok(Reputation(score))
        } else {
            Err(format!("Reputation must be between 0.0 and 1.0, got {}", score))
        }
    }

    /// Get score value
    pub fn score(&self) -> f64 {
        self.0
    }

    /// Default reputation for new agents
    pub fn default_new_agent() -> Self {
        Reputation(0.5) // Neutral start
    }
}

impl fmt::Display for Reputation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{:.2}", self.0)
    }
}

/// Confidence level (0.0 to 1.0)
#[derive(Debug, Clone, Copy, PartialEq, PartialOrd, Serialize, Deserialize)]
pub struct Confidence(f64);

impl Confidence {
    pub fn new(value: f64) -> Result<Self, String> {
        if (0.0..=1.0).contains(&value) {
            Ok(Confidence(value))
        } else {
            Err(format!("Confidence must be between 0.0 and 1.0, got {}", value))
        }
    }

    pub fn value(&self) -> f64 {
        self.0
    }

    /// Low confidence threshold
    pub fn is_low(&self) -> bool {
        self.0 < 0.5
    }

    /// High confidence threshold
    pub fn is_high(&self) -> bool {
        self.0 >= 0.8
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_reputation_bounds() {
        assert!(Reputation::new(0.0).is_ok());
        assert!(Reputation::new(1.0).is_ok());
        assert!(Reputation::new(0.5).is_ok());
        assert!(Reputation::new(-0.1).is_err());
        assert!(Reputation::new(1.1).is_err());
    }

    #[test]
    fn test_confidence_thresholds() {
        let low = Confidence::new(0.3).unwrap();
        assert!(low.is_low());
        assert!(!low.is_high());

        let high = Confidence::new(0.9).unwrap();
        assert!(!high.is_low());
        assert!(high.is_high());
    }
}

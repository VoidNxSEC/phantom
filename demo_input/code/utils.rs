//! Utility functions for PHANTOM
use std::collections::HashMap;

/// Hash a string with custom salt
pub fn hash_with_salt(input: &str, salt: &str) -> String {
    // Implementation here
    format!("{}-{}", input, salt)
}

pub fn process_data(data: &[u8]) -> Result<Vec<u8>, String> {
    Ok(data.to_vec())
}

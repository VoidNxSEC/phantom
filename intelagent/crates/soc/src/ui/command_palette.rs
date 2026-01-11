//! Command Palette - The brain of the SOC
//! Phase 0: Simple text entry + command execution

use gtk4::prelude::*;
use gtk4::{Box, Entry, Orientation};
use std::cell::RefCell;
use std::path::PathBuf;
use std::rc::Rc;

use crate::engine::PhantomAgent;

pub struct CommandPalette {
    container: Box,
    entry: Entry,
    history: Rc<RefCell<Vec<String>>>,
}

impl CommandPalette {
    pub fn new() -> Self {
        let container = Box::new(Orientation::Horizontal, 8);
        container.set_margin_top(8);
        container.set_margin_bottom(8);
        container.set_margin_start(12);
        container.set_margin_end(12);

        // Prompt symbol
        let prompt_label = gtk4::Label::new(Some(">"));
        prompt_label.add_css_class("monospace");
        prompt_label.set_opacity(0.7);
        container.append(&prompt_label);

        // Command entry
        let entry = Entry::builder()
            .placeholder_text("Enter command (e.g., process-document --file data.pdf)")
            .hexpand(true)
            .build();

        entry.add_css_class("command-entry");

        container.append(&entry);

        let history = Rc::new(RefCell::new(Vec::new()));

        // Connect activate (Enter key)
        let history_clone = history.clone();
        entry.connect_activate(move |e| {
            let text = e.text().to_string();
            if !text.is_empty() {
                tracing::info!("Command entered: {}", text);

                // Add to history
                history_clone.borrow_mut().push(text.clone());

                // Execute command
                Self::execute_command(&text);

                // Clear entry
                e.set_text("");
            }
        });

        Self {
            container,
            entry,
            history,
        }
    }

    pub fn widget(&self) -> &Box {
        &self.container
    }

    fn execute_command(cmd: &str) {
        tracing::info!("Executing command: {}", cmd);

        // Parse command (simple string splitting for Phase 0)
        let parts: Vec<&str> = cmd.split_whitespace().collect();

        if parts.is_empty() {
            tracing::warn!("Empty command");
            return;
        }

        let command = parts[0];
        let args = &parts[1..];

        match command {
            "process-document" => {
                Self::handle_process_document(args);
            }
            "help" => {
                Self::handle_help();
            }
            _ => {
                tracing::warn!("Unknown command: {}", command);
                // TODO: Show error in UI
            }
        }
    }

    fn handle_process_document(args: &[&str]) {
        // Parse --file argument
        let file_path = Self::parse_arg(args, "--file");

        if let Some(path) = file_path {
            tracing::info!("Processing document: {}", path);

            // Spawn async task to process file
            let path_buf = PathBuf::from(path);
            glib::spawn_future_local(async move {
                match PhantomAgent::new() {
                    Ok(agent) => {
                        tracing::info!("✅ PhantomAgent initialized: {}", agent.id());

                        match agent.process_file(path_buf.clone()).await {
                            Ok(result) => {
                                tracing::info!("✅ SUCCESS: Processed {:?}", path_buf);
                                tracing::info!("   Duration: {}ms", result.duration_ms);
                                tracing::info!("   Output: {}", result.output_dir);
                                if !result.stdout.is_empty() {
                                    tracing::info!("   Stdout: {}", result.stdout);
                                }
                            }
                            Err(e) => {
                                tracing::error!("❌ FAILED: {:?}", e);
                            }
                        }
                    }
                    Err(e) => {
                        tracing::error!("❌ Failed to initialize PhantomAgent: {:?}", e);
                    }
                }
            });
        } else {
            tracing::error!("Missing --file argument");
        }
    }

    fn handle_help() {
        tracing::info!("╔═══════════════════════════════════════════════════════╗");
        tracing::info!("║  AVAILABLE COMMANDS                                   ║");
        tracing::info!("╠═══════════════════════════════════════════════════════╣");
        tracing::info!("║  📄 process-document --file <path>                    ║");
        tracing::info!("║     Process document via Phantom engine               ║");
        tracing::info!("║                                                       ║");
        tracing::info!("║  ❓ help                                               ║");
        tracing::info!("║     Show this help message                            ║");
        tracing::info!("╚═══════════════════════════════════════════════════════╝");
    }

    fn parse_arg<'a>(args: &'a [&'a str], flag: &str) -> Option<&'a str> {
        args.windows(2).find(|w| w[0] == flag).map(|w| w[1])
    }
}

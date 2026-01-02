//! SOC Layout - Main window structure
//!
//! Layout:
//! ┌────────────────────────────────────────┐
//! │ TOP BAR (status + actions)             │
//! ├──────┬─────────────────────┬───────────┤
//! │ TREE │  WORKSPACE (4-split)│ INTEL     │
//! │      │                     │ PANEL     │
//! └──────┴─────────────────────┴───────────┘
//! │ COMMAND BAR                            │
//! └────────────────────────────────────────┘

use gtk4::prelude::*;
use gtk4::{Box as GtkBox, Orientation, Paned};

pub struct SOCLayout {
    pub container: GtkBox,
    pub main_paned: Paned,
    pub workspace_paned: Paned,
}

impl SOCLayout {
    pub fn new() -> Self {
        // Main vertical container
        let container = GtkBox::new(Orientation::Vertical, 0);

        // Top bar placeholder
        let top_bar = GtkBox::new(Orientation::Horizontal, 8);
        top_bar.set_height_request(40);
        top_bar.set_margin_start(12);
        top_bar.set_margin_end(12);
        top_bar.set_margin_top(8);

        let status_label = gtk4::Label::new(Some("⚡ SOC ONLINE | Agents: 0 | Intel: 0 | Alerts: 0"));
        status_label.add_css_class("status-label");
        top_bar.append(&status_label);

        container.append(&top_bar);

        // Main horizontal paned (left sidebar | center | right sidebar)
        let main_paned = Paned::new(Orientation::Horizontal);
        main_paned.set_vexpand(true);
        main_paned.set_position(250); // Left sidebar width

        // Left sidebar (Agent Tree) - 250px
        let left_sidebar = GtkBox::new(Orientation::Vertical, 0);
        left_sidebar.set_width_request(250);
        let left_label = gtk4::Label::new(Some("🤖 AGENT TREE"));
        left_label.add_css_class("panel-title");
        left_label.set_margin_top(8);
        left_sidebar.append(&left_label);

        // Placeholder for agent tree
        let tree_scroll = gtk4::ScrolledWindow::new();
        tree_scroll.set_vexpand(true);
        left_sidebar.append(&tree_scroll);

        main_paned.set_start_child(Some(&left_sidebar));

        // Center + Right paned
        let center_right_paned = Paned::new(Orientation::Horizontal);
        center_right_paned.set_position(800); // Center gets 800px

        // Center workspace (4-split)
        let workspace_paned = Self::create_workspace();
        center_right_paned.set_start_child(Some(&workspace_paned));

        // Right sidebar (Intel Panel) - 300px
        let right_sidebar = GtkBox::new(Orientation::Vertical, 0);
        right_sidebar.set_width_request(300);
        let right_label = gtk4::Label::new(Some("📊 INTEL PANEL"));
        right_label.add_css_class("panel-title");
        right_label.set_margin_top(8);
        right_sidebar.append(&right_label);

        // Placeholder for tabs
        let intel_scroll = gtk4::ScrolledWindow::new();
        intel_scroll.set_vexpand(true);
        right_sidebar.append(&intel_scroll);

        center_right_paned.set_end_child(Some(&right_sidebar));

        main_paned.set_end_child(Some(&center_right_paned));

        container.append(&main_paned);

        // Command bar (bottom)
        let command_bar = Self::create_command_bar();
        container.append(&command_bar);

        Self {
            container,
            main_paned,
            workspace_paned,
        }
    }

    fn create_workspace() -> Paned {
        // Vertical split first (top | bottom)
        let vertical_paned = Paned::new(Orientation::Vertical);
        vertical_paned.set_position(400);

        // Top horizontal split (Live Logs | Execution Tree)
        let top_paned = Paned::new(Orientation::Horizontal);
        top_paned.set_position(400);

        // Top-left: Live Logs
        let logs_box = GtkBox::new(Orientation::Vertical, 0);
        let logs_label = gtk4::Label::new(Some("📜 LIVE LOGS"));
        logs_label.add_css_class("workspace-title");
        logs_label.set_halign(gtk4::Align::Start);
        logs_label.set_margin_start(8);
        logs_label.set_margin_top(4);
        logs_box.append(&logs_label);

        let logs_scroll = gtk4::ScrolledWindow::new();
        logs_scroll.set_vexpand(true);
        let logs_view = gtk4::TextView::new();
        logs_view.set_editable(false);
        logs_view.set_monospace(true);
        logs_view.add_css_class("log-view");
        logs_scroll.set_child(Some(&logs_view));
        logs_box.append(&logs_scroll);

        top_paned.set_start_child(Some(&logs_box));

        // Top-right: Execution Tree
        let tree_box = GtkBox::new(Orientation::Vertical, 0);
        let tree_label = gtk4::Label::new(Some("🌳 EXECUTION TREE"));
        tree_label.add_css_class("workspace-title");
        tree_label.set_halign(gtk4::Align::Start);
        tree_label.set_margin_start(8);
        tree_label.set_margin_top(4);
        tree_box.append(&tree_label);

        let tree_area = gtk4::DrawingArea::new();
        tree_area.set_vexpand(true);
        tree_area.add_css_class("execution-tree");
        tree_box.append(&tree_area);

        top_paned.set_end_child(Some(&tree_box));

        vertical_paned.set_start_child(Some(&top_paned));

        // Bottom horizontal split (Agent Log | Intel Viz)
        let bottom_paned = Paned::new(Orientation::Horizontal);
        bottom_paned.set_position(400);

        // Bottom-left: Agent-specific Log
        let agent_log_box = GtkBox::new(Orientation::Vertical, 0);
        let agent_log_label = gtk4::Label::new(Some("🔍 AGENT LOG"));
        agent_log_label.add_css_class("workspace-title");
        agent_log_label.set_halign(gtk4::Align::Start);
        agent_log_label.set_margin_start(8);
        agent_log_label.set_margin_top(4);
        agent_log_box.append(&agent_log_label);

        let agent_log_scroll = gtk4::ScrolledWindow::new();
        agent_log_scroll.set_vexpand(true);
        let agent_log_view = gtk4::TextView::new();
        agent_log_view.set_editable(false);
        agent_log_view.set_monospace(true);
        agent_log_view.add_css_class("log-view");
        agent_log_scroll.set_child(Some(&agent_log_view));
        agent_log_box.append(&agent_log_scroll);

        bottom_paned.set_start_child(Some(&agent_log_box));

        // Bottom-right: Intel Visualizer
        let intel_viz_box = GtkBox::new(Orientation::Vertical, 0);
        let intel_viz_label = gtk4::Label::new(Some("🎯 INTEL VISUALIZER"));
        intel_viz_label.add_css_class("workspace-title");
        intel_viz_label.set_halign(gtk4::Align::Start);
        intel_viz_label.set_margin_start(8);
        intel_viz_label.set_margin_top(4);
        intel_viz_box.append(&intel_viz_label);

        let intel_viz_area = gtk4::DrawingArea::new();
        intel_viz_area.set_vexpand(true);
        intel_viz_area.add_css_class("intel-viz");
        intel_viz_box.append(&intel_viz_area);

        bottom_paned.set_end_child(Some(&intel_viz_box));

        vertical_paned.set_end_child(Some(&bottom_paned));

        vertical_paned
    }

    fn create_command_bar() -> GtkBox {
        let command_box = GtkBox::new(Orientation::Horizontal, 8);
        command_box.set_height_request(50);
        command_box.set_margin_start(12);
        command_box.set_margin_end(12);
        command_box.set_margin_bottom(8);
        command_box.add_css_class("command-bar");

        let prompt = gtk4::Label::new(Some(">"));
        prompt.add_css_class("command-prompt");
        command_box.append(&prompt);

        let entry = gtk4::Entry::new();
        entry.set_hexpand(true);
        entry.set_placeholder_text(Some("Enter command (e.g., agent-3 investigate target X)..."));
        entry.add_css_class("command-entry");
        command_box.append(&entry);

        command_box
    }

    pub fn widget(&self) -> &GtkBox {
        &self.container
    }
}

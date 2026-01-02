//! Log Viewer - Real-time log display
//! Phase 0: Simple text view showing logs

use gtk4::prelude::*;
use gtk4::{ScrolledWindow, TextView, TextBuffer};

pub struct LogViewer {
    container: ScrolledWindow,
    text_view: TextView,
    buffer: TextBuffer,
}

impl LogViewer {
    pub fn new() -> Self {
        let buffer = TextBuffer::new(None);

        let text_view = TextView::builder()
            .buffer(&buffer)
            .editable(false)
            .monospace(true)
            .top_margin(8)
            .bottom_margin(8)
            .left_margin(12)
            .right_margin(12)
            .build();

        let container = ScrolledWindow::builder()
            .child(&text_view)
            .vexpand(true)
            .build();

        // Initial message with style
        buffer.set_text("╔══════════════════════════════════════════════════════╗\n");
        buffer.insert_at_cursor("║  IntelAgent SOC - System Operations Center         ║\n");
        buffer.insert_at_cursor("║  Phase 0: Foundation                                ║\n");
        buffer.insert_at_cursor("╚══════════════════════════════════════════════════════╝\n\n");
        buffer.insert_at_cursor("✅ Status: OPERATIONAL\n");
        buffer.insert_at_cursor("🎯 Mode: Development\n");
        buffer.insert_at_cursor("🔧 Ready: Type 'help' to see available commands\n\n");

        Self {
            container,
            text_view,
            buffer,
        }
    }

    pub fn widget(&self) -> &ScrolledWindow {
        &self.container
    }

    pub fn append_log(&self, message: &str) {
        self.buffer.insert_at_cursor(&format!("{}\n", message));

        // Auto-scroll to bottom
        let mut end_iter = self.buffer.end_iter();
        self.text_view.scroll_to_iter(&mut end_iter, 0.0, false, 0.0, 0.0);
    }
}

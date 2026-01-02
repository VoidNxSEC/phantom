//! IntelAgent SOC - System Operations Center
//! Phase 0: Foundation - GTK4 app + Command palette + Phantom integration

use gtk4::prelude::*;
use gtk4::{Application, ApplicationWindow};
use libadwaita as adw;
use adw::prelude::*;

mod ui;
mod engine;
mod kernel;

use ui::SOCLayout;

const APP_ID: &str = "dev.voidnix.intelagent.soc";

fn main() -> anyhow::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt()
        .with_max_level(tracing::Level::DEBUG)
        .init();

    tracing::info!("Starting IntelAgent SOC...");

    // Initialize GTK4 + Adwaita
    adw::init().expect("Failed to initialize libadwaita");

    // Force dark theme (modern look)
    let style_manager = adw::StyleManager::default();
    style_manager.set_color_scheme(adw::ColorScheme::ForceDark);
    tracing::info!("Dark theme enabled");

    // Load custom CSS
    load_custom_css();

    // Create application
    let app = Application::builder()
        .application_id(APP_ID)
        .build();

    app.connect_activate(build_ui);

    // Run
    let _exit_code = app.run();

    Ok(())
}

fn load_custom_css() {
    let provider = gtk4::CssProvider::new();
    provider.load_from_string(include_str!("../style.css"));

    gtk4::style_context_add_provider_for_display(
        &gtk4::gdk::Display::default().expect("Could not connect to display"),
        &provider,
        gtk4::STYLE_PROVIDER_PRIORITY_APPLICATION,
    );

    tracing::info!("Custom CSS loaded");
}

fn build_ui(app: &Application) {
    // Create main window
    let window = ApplicationWindow::builder()
        .application(app)
        .title("IntelAgent SOC - Phantom Cyber Operations Center")
        .default_width(1600)
        .default_height(1000)
        .build();

    // Create SOC layout
    let soc_layout = SOCLayout::new();

    // Set main content (GTK4 uses set_child)
    window.set_child(Some(soc_layout.widget()));

    // Show window
    window.present();

    tracing::info!("SOC UI initialized");
}

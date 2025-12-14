#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  PHANTOM DESKTOP - Native GTK4/Adwaita Application              ║
║  ─────────────────────────────────────────────────────────────── ║
║  Pure Python + GTK4 + Libadwaita - NO WEB, NO ELECTRON           ║
║  • Document Intelligence Dashboard                                ║
║  • RAG Query Interface                                            ║
║  • Vector Search                                                  ║
║  • LLM Provider Configuration                                     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, Pango
import sys
import os
import threading
from pathlib import Path
from typing import Optional

# Phantom imports
try:
    from phantom.core import CortexProcessor, DocumentInsights
    from phantom.rag import FAISSVectorStore, SearchResult
    from phantom.providers import LlamaCppProvider, OllamaProvider
    PHANTOM_AVAILABLE = True
except ImportError:
    PHANTOM_AVAILABLE = False


VERSION = "2.0.0"
APP_ID = "dev.phantom.desktop"


class PhantomWindow(Adw.ApplicationWindow):
    """Main application window"""
    
    def __init__(self, app):
        super().__init__(application=app)
        
        self.set_title("Phantom Desktop")
        self.set_default_size(1200, 800)
        
        # Initialize processor
        self.processor: Optional[CortexProcessor] = None
        self._init_processor()
        
        # Build UI
        self._build_ui()
    
    def _init_processor(self):
        """Initialize Cortex processor in background"""
        if PHANTOM_AVAILABLE:
            try:
                self.processor = CortexProcessor(
                    enable_vectors=True,
                    verbose=False,
                )
            except Exception as e:
                print(f"Processor init failed: {e}")
    
    def _build_ui(self):
        """Build the main UI"""
        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)
        
        # Header bar
        header = Adw.HeaderBar()
        header.set_title_widget(Adw.WindowTitle(
            title="Phantom",
            subtitle="Document Intelligence"
        ))
        
        # Menu button
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu = Gio.Menu()
        menu.append("Settings", "app.settings")
        menu.append("About", "app.about")
        menu_button.set_menu_model(menu)
        header.pack_end(menu_button)
        
        # Open file button
        open_button = Gtk.Button(icon_name="document-open-symbolic")
        open_button.set_tooltip_text("Open Document")
        open_button.connect("clicked", self._on_open_clicked)
        header.pack_start(open_button)
        
        main_box.append(header)
        
        # Toast overlay for notifications
        self.toast_overlay = Adw.ToastOverlay()
        main_box.append(self.toast_overlay)
        
        # Content with navigation
        self.leaflet = Adw.Leaflet()
        self.leaflet.set_can_unfold(True)
        self.toast_overlay.set_child(self.leaflet)
        
        # Sidebar
        sidebar = self._build_sidebar()
        self.leaflet.append(sidebar)
        
        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.leaflet.append(sep)
        
        # Main content stack
        self.content_stack = Gtk.Stack()
        self.content_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.content_stack.set_hexpand(True)
        self.content_stack.set_vexpand(True)
        
        # Add pages
        self.content_stack.add_titled(self._build_dashboard_page(), "dashboard", "Dashboard")
        self.content_stack.add_titled(self._build_search_page(), "search", "Search")
        self.content_stack.add_titled(self._build_process_page(), "process", "Process")
        self.content_stack.add_titled(self._build_settings_page(), "settings", "Settings")
        
        self.leaflet.append(self.content_stack)
    
    def _build_sidebar(self) -> Gtk.Widget:
        """Build navigation sidebar"""
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar_box.set_size_request(200, -1)
        sidebar_box.add_css_class("sidebar")
        
        # Navigation list
        nav_list = Gtk.ListBox()
        nav_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        nav_list.add_css_class("navigation-sidebar")
        nav_list.connect("row-selected", self._on_nav_selected)
        
        pages = [
            ("view-dashboard-symbolic", "Dashboard", "dashboard"),
            ("system-search-symbolic", "Search", "search"),
            ("document-send-symbolic", "Process", "process"),
            ("emblem-system-symbolic", "Settings", "settings"),
        ]
        
        for icon, label, name in pages:
            row = Adw.ActionRow()
            row.set_title(label)
            row.add_prefix(Gtk.Image.new_from_icon_name(icon))
            row.set_name(name)
            nav_list.append(row)
        
        sidebar_box.append(nav_list)
        
        # Select first row
        nav_list.select_row(nav_list.get_row_at_index(0))
        
        return sidebar_box
    
    def _build_dashboard_page(self) -> Gtk.Widget:
        """Build dashboard page"""
        page = Adw.PreferencesPage()
        
        # Status group
        status_group = Adw.PreferencesGroup()
        status_group.set_title("System Status")
        status_group.set_description("Current Phantom status")
        
        # Provider status
        provider_row = Adw.ActionRow()
        provider_row.set_title("LLM Provider")
        if self.processor and self.processor.provider.is_available():
            provider_row.set_subtitle(f"✓ {self.processor.provider.name} connected")
            provider_row.add_suffix(Gtk.Image.new_from_icon_name("emblem-ok-symbolic"))
        else:
            provider_row.set_subtitle("⚠ No provider available")
            provider_row.add_suffix(Gtk.Image.new_from_icon_name("dialog-warning-symbolic"))
        status_group.add(provider_row)
        
        # Vector store status
        vector_row = Adw.ActionRow()
        vector_row.set_title("Vector Store")
        if self.processor and self.processor.vector_store:
            count = len(self.processor.vector_store)
            vector_row.set_subtitle(f"FAISS - {count} vectors indexed")
        else:
            vector_row.set_subtitle("Not initialized")
        status_group.add(vector_row)
        
        page.add(status_group)
        
        # Quick actions group
        actions_group = Adw.PreferencesGroup()
        actions_group.set_title("Quick Actions")
        
        # Process directory button
        process_row = Adw.ActionRow()
        process_row.set_title("Process Documents")
        process_row.set_subtitle("Extract insights from a directory")
        process_btn = Gtk.Button(label="Select Folder")
        process_btn.set_valign(Gtk.Align.CENTER)
        process_btn.connect("clicked", self._on_process_folder)
        process_row.add_suffix(process_btn)
        actions_group.add(process_row)
        
        page.add(actions_group)
        
        return page
    
    def _build_search_page(self) -> Gtk.Widget:
        """Build semantic search page"""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)
        
        # Title
        title = Gtk.Label(label="Semantic Search")
        title.add_css_class("title-1")
        title.set_halign(Gtk.Align.START)
        box.append(title)
        
        # Search entry
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Enter your query...")
        self.search_entry.set_hexpand(True)
        self.search_entry.connect("activate", self._on_search)
        search_box.append(self.search_entry)
        
        search_btn = Gtk.Button(label="Search")
        search_btn.add_css_class("suggested-action")
        search_btn.connect("clicked", self._on_search)
        search_box.append(search_btn)
        
        box.append(search_box)
        
        # Results list
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.results_list = Gtk.ListBox()
        self.results_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.results_list.add_css_class("boxed-list")
        scroll.set_child(self.results_list)
        
        box.append(scroll)
        
        return box
    
    def _build_process_page(self) -> Gtk.Widget:
        """Build document processing page"""
        page = Adw.PreferencesPage()
        
        group = Adw.PreferencesGroup()
        group.set_title("Process Documents")
        group.set_description("Extract insights from markdown files")
        
        # Input path
        input_row = Adw.EntryRow()
        input_row.set_title("Input Path")
        self.input_entry = input_row
        group.add(input_row)
        
        # Output path
        output_row = Adw.EntryRow()
        output_row.set_title("Output Path")
        self.output_entry = output_row
        group.add(output_row)
        
        # Chunk size
        chunk_row = Adw.SpinRow.new_with_range(256, 2048, 128)
        chunk_row.set_title("Chunk Size (tokens)")
        chunk_row.set_value(1024)
        group.add(chunk_row)
        
        # Process button
        process_btn = Gtk.Button(label="Start Processing")
        process_btn.add_css_class("suggested-action")
        process_btn.set_margin_top(16)
        process_btn.connect("clicked", self._on_start_processing)
        
        page.add(group)
        
        # Progress
        progress_group = Adw.PreferencesGroup()
        progress_group.set_title("Progress")
        
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_margin_start(12)
        self.progress_bar.set_margin_end(12)
        self.progress_bar.set_margin_top(12)
        self.progress_bar.set_margin_bottom(12)
        progress_group.add(self.progress_bar)
        
        page.add(progress_group)
        
        return page
    
    def _build_settings_page(self) -> Gtk.Widget:
        """Build settings page"""
        page = Adw.PreferencesPage()
        
        # Provider group
        provider_group = Adw.PreferencesGroup()
        provider_group.set_title("LLM Provider")
        
        # LlamaCPP URL
        llama_row = Adw.EntryRow()
        llama_row.set_title("LlamaCPP URL")
        llama_row.set_text("http://localhost:8080")
        provider_group.add(llama_row)
        
        # Ollama URL
        ollama_row = Adw.EntryRow()
        ollama_row.set_title("Ollama URL")
        ollama_row.set_text("http://localhost:11434")
        provider_group.add(ollama_row)
        
        page.add(provider_group)
        
        # Vector DB group
        vector_group = Adw.PreferencesGroup()
        vector_group.set_title("Vector Database")
        
        # Embedding model
        embed_row = Adw.EntryRow()
        embed_row.set_title("Embedding Model")
        embed_row.set_text("all-MiniLM-L6-v2")
        vector_group.add(embed_row)
        
        # Index path
        index_row = Adw.EntryRow()
        index_row.set_title("Index Path")
        index_row.set_text("/var/lib/phantom/vectors")
        vector_group.add(index_row)
        
        page.add(vector_group)
        
        return page
    
    def _on_nav_selected(self, listbox, row):
        """Handle navigation selection"""
        if row:
            self.content_stack.set_visible_child_name(row.get_name())
    
    def _on_open_clicked(self, button):
        """Handle open file button"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Open Document")
        
        filter_md = Gtk.FileFilter()
        filter_md.set_name("Markdown files")
        filter_md.add_pattern("*.md")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_md)
        dialog.set_filters(filters)
        
        dialog.open(self, None, self._on_file_opened)
    
    def _on_file_opened(self, dialog, result):
        """Handle file opened"""
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                self._process_file(Path(path))
        except Exception as e:
            self._show_toast(f"Error: {e}")
    
    def _on_process_folder(self, button):
        """Handle folder selection for processing"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Select Folder")
        dialog.select_folder(self, None, self._on_folder_selected)
    
    def _on_folder_selected(self, dialog, result):
        """Handle folder selected"""
        try:
            file = dialog.select_folder_finish(result)
            if file:
                path = file.get_path()
                self.input_entry.set_text(path)
                self.content_stack.set_visible_child_name("process")
        except Exception as e:
            self._show_toast(f"Error: {e}")
    
    def _on_search(self, widget):
        """Perform semantic search"""
        query = self.search_entry.get_text().strip()
        if not query:
            return
        
        if not self.processor or not self.processor.vector_store:
            self._show_toast("Vector store not available")
            return
        
        # Clear previous results
        while True:
            child = self.results_list.get_row_at_index(0)
            if child:
                self.results_list.remove(child)
            else:
                break
        
        # Search
        try:
            results = self.processor.search(query, top_k=5)
            
            for i, result in enumerate(results):
                row = Adw.ActionRow()
                row.set_title(f"Result {i + 1} (score: {result.score:.3f})")
                row.set_subtitle(result.text[:200] + "...")
                self.results_list.append(row)
            
            if not results:
                self._show_toast("No results found")
        except Exception as e:
            self._show_toast(f"Search error: {e}")
    
    def _on_start_processing(self, button):
        """Start document processing"""
        input_path = self.input_entry.get_text()
        output_path = self.output_entry.get_text()
        
        if not input_path or not output_path:
            self._show_toast("Please specify input and output paths")
            return
        
        # Process in background thread
        thread = threading.Thread(
            target=self._process_directory,
            args=(Path(input_path), Path(output_path))
        )
        thread.daemon = True
        thread.start()
    
    def _process_file(self, filepath: Path):
        """Process a single file"""
        if not self.processor:
            self._show_toast("Processor not available")
            return
        
        def do_process():
            try:
                result = self.processor.process_document(filepath)
                GLib.idle_add(
                    self._show_toast,
                    f"Processed: {result.file_name} ({len(result.themes)} themes)"
                )
            except Exception as e:
                GLib.idle_add(self._show_toast, f"Error: {e}")
        
        thread = threading.Thread(target=do_process)
        thread.daemon = True
        thread.start()
    
    def _process_directory(self, input_path: Path, output_path: Path):
        """Process directory in background"""
        try:
            files = list(input_path.rglob("*.md"))
            total = len(files)
            
            for i, filepath in enumerate(files):
                result = self.processor.process_document(filepath)
                
                progress = (i + 1) / total
                GLib.idle_add(self.progress_bar.set_fraction, progress)
                GLib.idle_add(
                    self.progress_bar.set_text,
                    f"{i + 1}/{total}: {filepath.name}"
                )
            
            GLib.idle_add(self._show_toast, f"Processed {total} files")
        except Exception as e:
            GLib.idle_add(self._show_toast, f"Error: {e}")
    
    def _show_toast(self, message: str):
        """Show a toast notification"""
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)


class PhantomApp(Adw.Application):
    """Main application class"""
    
    def __init__(self):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS,
        )
        
        # Setup actions
        self.create_action("quit", self.on_quit, ["<Ctrl>q"])
        self.create_action("about", self.on_about)
        self.create_action("settings", self.on_settings)
    
    def do_activate(self):
        """Activate the application"""
        win = self.props.active_window
        if not win:
            win = PhantomWindow(self)
        win.present()
    
    def on_quit(self, action, param):
        """Quit the application"""
        self.quit()
    
    def on_about(self, action, param):
        """Show about dialog"""
        about = Adw.AboutDialog(
            application_name="Phantom Desktop",
            application_icon=APP_ID,
            developer_name="kernelcore",
            version=VERSION,
            developers=["kernelcore"],
            copyright="© 2024 VoidNix",
            website="https://github.com/kernelcore/phantom",
            issue_url="https://github.com/kernelcore/phantom/issues",
            license_type=Gtk.License.MIT_X11,
            comments="AI-Powered Document Intelligence",
        )
        about.present(self.props.active_window)
    
    def on_settings(self, action, param):
        """Open settings"""
        win = self.props.active_window
        if win:
            win.content_stack.set_visible_child_name("settings")
    
    def create_action(self, name, callback, shortcuts=None):
        """Create an application action"""
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main():
    """Main entry point"""
    app = PhantomApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    main()

"""
GUI Helpers - Utilities for enhancing the GUI with Instagram link functionality.
Provides components for integrating the LinkProcessor with the GUI.
"""
import tkinter as tk
from tkinter import scrolledtext
import re
from typing import Callable, List, Optional, Any

from utils.link_processor import LinkProcessor, create_link_processor

class InstagramLinkMenu:
    """
    Adds context menu functionality to text widgets for handling Instagram links.
    
    Features:
    1. Right-click context menu for Instagram links
    2. Actions: Open link in browser, copy link
    3. Link highlighting
    """
    
    def __init__(self, text_widget: scrolledtext.ScrolledText, link_processor: LinkProcessor):
        self.text_widget = text_widget
        self.link_processor = link_processor
        self.context_menu = tk.Menu(text_widget, tearoff=0)
        
        # Bind right-click event (Button-3)
        self.text_widget.bind("<Button-3>", self._show_context_menu)
        
        # Configure link highlighting
        self.text_widget.tag_configure("instagram_link", foreground="blue", underline=1)
    
    def _show_context_menu(self, event: tk.Event) -> None:
        """Show context menu if cursor is over an Instagram link."""
        index = self.text_widget.index(f"@{event.x},{event.y}")
        self.selected_link = None
        
        # Check if cursor is over a tagged link
        if self.text_widget.tag_names(index) == ("instagram_link",):
            # Extract link text under cursor
            start, end = self.text_widget.tag_prevrange("instagram_link", index)
            if start and end:
                self.selected_link = self.text_widget.get(start, end)
                self.context_menu.post(event.x_root, event.y_root)
    
    def _open_selected_link(self) -> None:
        """Open selected Instagram link in browser."""
        if self.selected_link:
            self.link_processor.open_instagram_link(self.selected_link)
    
    def _copy_selected_link(self) -> None:
        """Copy selected Instagram link to clipboard."""
        if self.selected_link:
            self.text_widget.clipboard_clear()
            self.text_widget.clipboard_append(self.selected_link)
    
    def _clear_menu(self) -> None:
        """Unpost the context menu."""
        self.context_menu.unpost()
    
    def highlight_links(self, text_content: str) -> None:
        """Highlight Instagram links in the text widget efficiently."""
        # Clear existing highlights
        self.text_widget.tag_remove("instagram_link", "1.0", tk.END)
        
        # Find all Instagram links
        for match in self.link_processor.INSTAGRAM_URL_PATTERN.finditer(text_content):
            start_idx = f"{match.start()//85}.{match.start()%85}"  # Example index calculation (simplified)
            end_idx = f"{match.end()//85}.{match.end()%85}"
            self.text_widget.tag_add("instagram_link", start_idx, end_idx)

def enhance_text_widget(text_widget: scrolledtext.ScrolledText, parent_window: Optional[tk.Tk] = None) -> InstagramLinkMenu:
    """
    Enhance a text widget with Instagram link functionality.
    
    Args:
        text_widget: The text widget to enhance
        parent_window: Parent window for error messages
        
    Returns:
        Configured InstagramLinkMenu instance
    """
    link_processor = create_link_processor(parent_window)
    return InstagramLinkMenu(text_widget, link_processor)
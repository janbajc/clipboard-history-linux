#!/bin/bash
# Simple setup script for Linux Clipboard History Manager (xclip-only version)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/.local/bin"
SERVICE_DIR="$HOME/.config/systemd/user"

echo "Setting up Linux Clipboard History Manager (xclip-only version)..."

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$SERVICE_DIR"

# Install xclip if needed
echo "Checking xclip installation..."
if ! command -v xclip >/dev/null 2>&1; then
    echo "Installing xclip..."
    if command -v apt >/dev/null 2>&1; then
        sudo apt update
        sudo apt install -y xclip
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --needed xclip
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y xclip
    else
        echo "Please install xclip manually for your distribution"
        exit 1
    fi
else
    echo "xclip is already installed ✓"
fi

# Check if we have the xclip version
if [ ! -f "clipboard_history_xclip.py" ]; then
    echo "Error: clipboard_history_xclip.py not found!"
    echo "Please make sure both setup files are in the same directory."
    exit 1
fi

# Copy the xclip-only script
echo "Installing clipboard history script..."
cp clipboard_history_xclip.py "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/clipboard_history_xclip.py"

# Test that it works
echo "Testing clipboard history script..."
if python3 "$INSTALL_DIR/clipboard_history_xclip.py" --list >/dev/null 2>&1; then
    echo "Script test successful ✓"
else
    echo "Warning: Script test failed. Check Python3 installation."
fi

# Create systemd user service
echo "Creating systemd service..."
cat > "$SERVICE_DIR/clipboard-history.service" << EOF
[Unit]
Description=Clipboard History Manager
After=graphical-session.target

[Service]
Type=simple
ExecStart=$INSTALL_DIR/clipboard_history_xclip.py --daemon
Restart=always
RestartSec=3
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
EOF

# Create desktop entry for GUI
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

echo "Creating desktop entry..."
cat > "$DESKTOP_DIR/clipboard-history.desktop" << EOF
[Desktop Entry]
Name=Clipboard History
Comment=View and manage clipboard history
Exec=$INSTALL_DIR/clipboard_history_xclip.py --gui
Icon=edit-copy
Terminal=false
Type=Application
Categories=Utility;
EOF

# Create keyboard shortcut script
echo "Creating shortcut launcher..."
cat > "$INSTALL_DIR/clipboard-history-gui" << EOF
#!/bin/bash
# Quick launcher for clipboard history GUI
python3 ~/.local/bin/clipboard_history_xclip.py --gui
EOF

chmod +x "$INSTALL_DIR/clipboard-history-gui"

echo ""
echo "Installation complete! 🎉"
echo ""
echo "Next steps:"
echo "1. Start the clipboard monitoring service:"
echo "   systemctl --user enable clipboard-history.service"
echo "   systemctl --user start clipboard-history.service"
echo ""
echo "2. Test the GUI:"
echo "   ~/.local/bin/clipboard_history_xclip.py --gui"
echo ""
echo "3. Set up keyboard shortcut (optional):"
echo "   - Go to Settings → Keyboard → Custom Shortcuts"
echo "   - Add command: ~/.local/bin/clipboard-history-gui"
echo "   - Assign to Super+V (or your preferred key)"
echo ""
echo "4. Check service status:"
echo "   systemctl --user status clipboard-history.service"
echo ""
echo "Usage:"
echo "  ~/.local/bin/clipboard_history_xclip.py --gui    # GUI version"
echo "  ~/.local/bin/clipboard_history_xclip.py --list   # Terminal list"
echo ""
echo "The clipboard history is stored in: ~/.clipboard_history.json"
#!/bin/bash
# Setup script for installing Chrome/Chromium on Vast AI

echo "Installing Chromium browser..."

# Update package list
apt-get update

# Install Chromium and dependencies
apt-get install -y chromium-browser chromium-chromedriver

# Verify installation
if command -v chromium-browser &> /dev/null; then
    echo "Chromium installed successfully at: $(which chromium-browser)"
else
    echo "Chromium installation failed. Trying alternative method..."
    
    # Alternative: Install Google Chrome
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
    apt-get update
    apt-get install -y google-chrome-stable
    
    if command -v google-chrome-stable &> /dev/null; then
        echo "Google Chrome installed successfully at: $(which google-chrome-stable)"
    else
        echo "Chrome installation failed. Please install manually."
        exit 1
    fi
fi

echo "Setup complete!"


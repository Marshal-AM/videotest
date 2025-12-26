#!/bin/bash
# Setup script for installing Chrome/Chromium on Vast AI

echo "Installing Chromium browser and dependencies..."

# Update package list
apt-get update

# Install Chromium, chromedriver, and required dependencies
apt-get install -y \
    chromium-browser \
    chromium-chromedriver \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2

# Make chromedriver executable if it exists
if [ -f /usr/bin/chromedriver ]; then
    chmod +x /usr/bin/chromedriver
    echo "Made chromedriver executable"
fi

# Verify installation
if command -v chromium-browser &> /dev/null; then
    echo "Chromium installed successfully at: $(which chromium-browser)"
    if command -v chromedriver &> /dev/null; then
        echo "Chromedriver found at: $(which chromedriver)"
    else
        echo "Warning: chromedriver not found in PATH, but may be installed"
    fi
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


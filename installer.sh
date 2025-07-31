#!/bin/bash

## setup command=wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/SimpleZooomPanel/main/installer.sh -O - | /bin/sh

## Only These 2 lines to edit with new version ######
version='2.2.7'
changelog='\nFix Server'
##############################################################

TMPPATH=/tmp/SimpleZooomPanel-main
FILEPATH=/tmp/main.tar.gz

# Determine plugin path based on architecture
if [ ! -d /usr/lib64 ]; then
    PLUGINPATH=/usr/lib/enigma2/python/Plugins/Extensions/SimpleZOOMPanel
else
    PLUGINPATH=/usr/lib64/enigma2/python/Plugins/Extensions/SimpleZOOMPanel
fi

# Detect OS type
if [ -f /var/lib/dpkg/status ]; then
    STATUS=/var/lib/dpkg/status
    OSTYPE=DreamOs
else
    STATUS=/var/lib/opkg/status
    OSTYPE=Dream
fi

echo ""

# Detect Python version
if python --version 2>&1 | grep -q '^Python 3\.'; then
    echo "You have Python3 image"
    PYTHON=PY3
    Packagesix=python3-six
    Packagerequests=python3-requests
else
    echo "You have Python2 image"
    PYTHON=PY2
    Packagerequests=python-requests
fi

# Install required packages
if [ "$PYTHON" = "PY3" ]; then
    if ! grep -qs "Package: $Packagesix" "$STATUS"; then
        opkg update && opkg --force-reinstall --force-overwrite install python3-six
    fi
fi

if ! grep -qs "Package: $Packagerequests" "$STATUS"; then
    echo "Need to install $Packagerequests"
    echo ""
    if [ "$OSTYPE" = "DreamOs" ]; then
        apt-get update && apt-get install -y python-requests
    elif [ "$PYTHON" = "PY3" ]; then
        opkg update && opkg --force-reinstall --force-overwrite install python3-requests
    else
        opkg update && opkg --force-reinstall --force-overwrite install python-requests
    fi
fi

echo ""

# Prepare environment
mkdir -p "$TMPPATH"
cd "$TMPPATH"

if [ "$OSTYPE" = "DreamOs" ]; then
    echo "# Your image is OE2.5/2.6 #"
else
    echo "# Your image is OE2.0 #"
fi

# Install additional dependencies for non-DreamOS
if [ "$OSTYPE" != "DreamOs" ]; then
    opkg update && opkg --force-reinstall --force-overwrite install ffmpeg gstplayer exteplayer3 enigma2-plugin-systemplugins-serviceapp
fi

sleep 2

# Download plugin package
wget --no-check-certificate --no-cache --no-dns-cache 'https://github.com/Belfagor2005/SimpleZooomPanel/archive/refs/heads/main.tar.gz'
tar -xzf main.tar.gz

# Find correct extracted directory
EXTRACTED_DIR=$(find . -maxdepth 1 -type d -name "SimpleZooomPanel-*")
if [ ! -d "$EXTRACTED_DIR/usr" ]; then
    echo "Extraction failed or 'usr' directory not found!"
    exit 1
fi

# Copy files
cp -r "$EXTRACTED_DIR/usr" "/"
cd
sleep 2

# Verify installation
if [ ! -d "$PLUGINPATH" ]; then
    echo "Some thing wrong .. Plugin not installed"
    rm -rf "$TMPPATH" > /dev/null 2>&1
    exit 1
fi

# Cleanup
rm -rf "$TMPPATH" > /dev/null 2>&1
sync

# Final messages
echo ""
echo ""
echo "#########################################################"
echo "#       SimpleZooomPanel INSTALLED SUCCESSFULLY        #"
echo "#                developed by LULULLA                   #"
echo "#                                                       #"
echo "#                  https://corvoboys.org                #"
echo "#########################################################"
echo "#           your Device will RESTART Now                #"
echo "#########################################################"

sleep 5
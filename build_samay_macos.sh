#!/bin/bash

# Samay Core Engine Build Script
# This script automates the complete build process for macOS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python() {
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
        print_status "Found Python $PYTHON_VERSION"
        
        # Check if version is 3.11 or higher
        if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
            print_success "Python version is compatible (3.11+)"
        else
            print_error "Python 3.11+ is required. Found: $PYTHON_VERSION"
            exit 1
        fi
    else
        print_error "Python 3 is not installed"
        exit 1
    fi
}

# Function to clean previous builds
clean_build() {
    print_status "Cleaning previous builds..."
    
    # Check if venv exists and is working
    if [ -d "venv" ] && [ -f "venv/bin/python3" ] && [ -x "venv/bin/python3" ]; then
        print_success "Virtual environment already exists and is working - keeping it"
    else
        # Remove old virtual environment only if it's broken
        if [ -d "venv" ]; then
            rm -rf venv
            print_success "Removed broken virtual environment"
        fi
    fi
    
    if [ -d "build" ]; then
        rm -rf build
        print_success "Removed old build directory"
    fi
    
    if [ -d "dist" ]; then
        rm -rf dist
        print_success "Removed old dist directory"
    fi
    
    if [ -d "src" ]; then
        rm -rf src
        print_success "Removed old src directory"
    fi
    
    if [ -f "temp_samay.dmg" ]; then
        rm -f temp_samay.dmg
        print_success "Removed old temporary DMG file"
    fi
}

# Function to setup virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    # Check if venv already exists and is working (unless force recreate is requested)
    if [ "$FORCE_RECREATE_VENV" != "true" ] && [ -d "venv" ] && [ -f "venv/bin/python3" ] && [ -x "venv/bin/python3" ]; then
        # Test if the venv is actually functional
        if venv/bin/python3 -c "import sys; print('OK')" >/dev/null 2>&1; then
            print_success "Virtual environment already exists and is working - skipping creation"
            print_status "Checking if dependencies are installed..."
            
            # Check if key dependencies are installed
            if venv/bin/python3 -c "import PyQt6, flask, pyinstaller" >/dev/null 2>&1; then
                print_success "Key dependencies are already installed - using existing venv"
                return 0
            else
                print_warning "Virtual environment exists but missing dependencies - will reinstall"
            fi
        else
            print_warning "Virtual environment exists but is broken - will recreate"
        fi
    fi
    
    print_status "Creating virtual environment..."
    
    # Retry venv creation up to 3 times
    local venv_created=false
    for attempt in 1 2 3; do
        print_status "Attempting to create virtual environment (attempt $attempt/3)..."
        
        # Remove any partial venv from previous attempts
        if [ $attempt -gt 1 ] && [ -d "venv" ]; then
            rm -rf venv
            print_status "Cleaned up partial virtual environment from previous attempt"
        fi
        
        python3 -m venv venv
        
        # Check if venv creation was successful
        if [ $? -eq 0 ] && [ -d "venv" ] && [ -f "venv/bin/python3" ]; then
            print_success "Virtual environment created successfully (attempt $attempt)"
            venv_created=true
            break
        else
            print_warning "Virtual environment creation failed (attempt $attempt/3)"
            if [ $attempt -lt 3 ]; then
                print_status "Retrying in 3 seconds..."
                sleep 3
            fi
        fi
    done
    
    # Check if venv was created successfully
    if [ "$venv_created" != "true" ]; then
        print_error "Failed to create virtual environment after 3 attempts"
        print_error "Checking if venv directory exists:"
        ls -la venv/ 2>/dev/null || echo "venv directory does not exist"
        print_error "Please check your Python installation and try again"
        exit 1
    fi
    
    print_status "Virtual environment created, waiting for it to be ready..."
    
    # Wait for venv to be fully created and verify it exists
    local max_attempts=20
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if [ -f "venv/bin/python3" ] && [ -x "venv/bin/python3" ]; then
            print_success "Virtual environment created successfully (attempt $attempt)"
            break
        fi
        
        print_status "Waiting for virtual environment... (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt + 1))
    done
    
    # Verify venv was created successfully
    if [ ! -f "venv/bin/python3" ] || [ ! -x "venv/bin/python3" ]; then
        print_error "Failed to create virtual environment after $max_attempts attempts"
        print_error "Checking venv directory contents:"
        ls -la venv/ 2>/dev/null || echo "venv directory does not exist"
        exit 1
    fi
    
    print_status "Upgrading pip..."
    
    # Wait for pip to be available
    local pip_attempts=0
    while [ $pip_attempts -lt 10 ]; do
        if venv/bin/python3 -m pip --version >/dev/null 2>&1; then
            break
        fi
        print_status "Waiting for pip to be available... ($pip_attempts/10)"
        sleep 1
        pip_attempts=$((pip_attempts + 1))
    done
    
    venv/bin/python3 -m pip install --upgrade pip
    
    print_success "Virtual environment created successfully"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing core dependencies..."
    
    venv/bin/pip install PyQt6 flask flask-restx flask-cors werkzeug pyinstaller requests
    
    print_status "Installing project modules..."
    venv/bin/pip install -e aw-core
    venv/bin/pip install -e aw-client
    venv/bin/pip install -e aw-server
    venv/bin/pip install -e aw-qt
    venv/bin/pip install -e aw-notify
    venv/bin/pip install -e aw-watcher-window
    
    print_success "All dependencies installed"
}

# Function to fix missing static directory
fix_static_directory() {
    print_status "Creating missing static directory..."
    
    mkdir -p aw-server/aw_server/static
    
    print_success "Static directory created"
}

# Function to build the app
build_app() {
    print_status "Building Samay macOS app..."
    
    venv/bin/pyinstaller --clean --noconfirm aw.spec
    
    print_success "Build completed successfully!"
}

# Function to verify build
verify_build() {
    print_status "Verifying build..."
    
    if [ -d "dist/Samay.app" ]; then
        print_success "Samay.app bundle created successfully"
        
        # Organize the build output
        print_status "Organizing build output..."
        mkdir -p dist/app dist/components dist/installers/macos
        
        # Move app bundle to organized structure
        mv dist/Samay.app dist/app/
        
        # Move individual components to components folder
        mv dist/aw-* dist/components/ 2>/dev/null || true
        
        # Check app size
        APP_SIZE=$(du -sh dist/app/Samay.app | cut -f1)
        print_status "App bundle size: $APP_SIZE"
        
        # List main components
        print_status "Build components:"
        ls -la dist/app/ dist/components/ dist/installers/ 2>/dev/null || echo "Components organized in subdirectories"
        
    else
        print_error "Samay.app bundle not found!"
        exit 1
    fi
}

# Function to create DMG (optional)
create_dmg() {
    if command_exists hdiutil; then
        print_status "Creating DMG installer..."
        
        # Create installers directory if it doesn't exist
        mkdir -p dist/installers/macos
        
        # Create temporary DMG
        TEMP_DMG="temp_samay.dmg"
        DMG_NAME="dist/installers/macos/Samay-$(date +%Y%m%d).dmg"
        
        hdiutil create -srcfolder dist/app/Samay.app -volname "Samay" -fs HFS+ -fsargs "-c c=64,a=16,e=16" -format UDRW -size 200m "$TEMP_DMG"
        
        # Mount and customize
        DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen "$TEMP_DMG" | egrep '^/dev/' | sed 1q | awk '{print $1}')
        
        # Unmount and convert to final DMG
        hdiutil detach "$DEVICE"
        hdiutil convert "$TEMP_DMG" -format UDZO -imagekey zlib-level=9 -o "$DMG_NAME"
        
        rm "$TEMP_DMG"
        
        print_success "DMG created: $DMG_NAME"
    else
        print_warning "hdiutil not found, skipping DMG creation"
    fi
}

# Function to show usage
show_usage() {
    echo "Samay Core Engine Build Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --clean-only           Only clean previous builds"
    echo "  --no-dmg               Skip DMG creation"
    echo "  --force-recreate-venv  Force recreation of virtual environment"
    echo "  --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                        # Full build process"
    echo "  $0 --clean-only           # Only clean"
    echo "  $0 --no-dmg               # Build without DMG"
    echo "  $0 --force-recreate-venv  # Force recreate venv (useful for dependency updates)"
}

# Main build function
main() {
    local CREATE_DMG=true
    local CLEAN_ONLY=false
    local FORCE_RECREATE_VENV=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean-only)
                CLEAN_ONLY=true
                shift
                ;;
            --no-dmg)
                CREATE_DMG=false
                shift
                ;;
            --force-recreate-venv)
                FORCE_RECREATE_VENV=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_status "Starting Samay Core Engine build process..."
    echo ""
    
    # Check prerequisites
    check_python
    
    # Clean previous builds
    clean_build
    
    if [ "$CLEAN_ONLY" = true ]; then
        print_success "Clean completed. Exiting."
        exit 0
    fi
    
    # Setup environment
    setup_venv
    
    # Install dependencies
    install_dependencies
    
    # Fix static directory
    fix_static_directory
    
    # Build the app
    build_app
    
    # Verify build
    verify_build
    
    # Create DMG if requested
    if [ "$CREATE_DMG" = true ]; then
        create_dmg
    fi
    
    echo ""
    print_success "🎉 Samay Core Engine build completed successfully!"
    print_status ""
    print_status "📦 Distribution Files:"
    print_status "  • DMG Installer: dist/installers/macos/Samay-$(date +%Y%m%d).dmg (for users)"
    print_status "  • App Bundle: dist/app/Samay.app (for development)"
    print_status ""
    print_status "🚀 For Users: Share the DMG file - they can drag & drop to install"
    print_status "🔧 For Development: Use dist/Samay.app for testing"
}

# Run main function with all arguments
main "$@"

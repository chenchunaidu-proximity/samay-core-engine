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
    
    if [ -d "venv" ]; then
        rm -rf venv
        print_success "Removed old virtual environment"
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
    
    python3 -m venv venv
    
    # Wait a moment for venv to be fully created
    sleep 1
    
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    print_success "Virtual environment created and activated"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing core dependencies..."
    
    pip install PyQt6 flask flask-restx flask-cors werkzeug pyinstaller requests
    
    print_status "Installing project modules..."
    pip install -e aw-core
    pip install -e aw-client
    pip install -e aw-server
    pip install -e aw-qt
    pip install -e aw-notify
    pip install -e aw-watcher-window
    
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
    
    pyinstaller --clean --noconfirm aw.spec
    
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
    echo "  --clean-only    Only clean previous builds"
    echo "  --no-dmg        Skip DMG creation"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0              # Full build process"
    echo "  $0 --clean-only # Only clean"
    echo "  $0 --no-dmg     # Build without DMG"
}

# Main build function
main() {
    local CREATE_DMG=true
    local CLEAN_ONLY=false
    
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

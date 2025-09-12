# Samay Core Engine

A privacy-focused desktop application for automated time tracking and activity monitoring. Built on the ActivityWatch foundation with custom branding and enhanced authentication features.

## Quick Start

### Automated Build (Recommended)

```bash
# Production build (default)
./build_samay_macos.sh

# QA build
./build_samay_macos.sh qa

# Production build (explicit)
./build_samay_macos.sh prod
```

### Build Options

```bash
# Show all options
./build_samay_macos.sh --help

# Clean previous builds only
./build_samay_macos.sh --clean-only

# Build without creating DMG
./build_samay_macos.sh --no-dmg
```

## Testing

```bash
# Test production environment (default)
./tests/run_tests.sh

# Test QA environment
./tests/run_tests.sh qa

# Test production environment (explicit)
./tests/run_tests.sh prod
```

## Build Output

This will create:
- **DMG Installer**: `dist/installers/macos/Samay-YYYY_MM_DD_t_HH_MM_SS.dmg` (for macOS users)
- **App Bundle**: `dist/app/Samay.app` (for development)

*Linux and Windows builds coming soon*

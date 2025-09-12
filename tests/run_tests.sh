#!/bin/bash

# Samay Core Engine Test Runner
# Centralized test runner with environment variable management

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

# Function to show usage
show_usage() {
    echo "Samay Core Engine Test Runner"
    echo ""
    echo "Usage: $0 [ENVIRONMENT] [OPTIONS]"
    echo ""
    echo "Environments:"
    echo "  qa                     Test QA environment (localhost:3001)"
    echo "  prod                   Test Production environment (default)"
    echo ""
    echo "Options:"
    echo "  --help, -h             Show this help message"
    echo "  --list-tests           List available test files"
    echo ""
    echo "Examples:"
    echo "  $0                        # Test prod environment"
    echo "  $0 qa                     # Test QA environment"
    echo "  $0 --list-tests           # List available tests"
}

# Function to list available test files
list_tests() {
    echo "Available test files:"
    echo ""
    
    tests_dir="$(dirname "$0")"
    if [ -d "$tests_dir" ]; then
        for test_file in "$tests_dir"/*.py; do
            if [ -f "$test_file" ]; then
                basename_test=$(basename "$test_file")
                echo "  • $basename_test"
            fi
        done
    else
        print_error "Tests directory not found: $tests_dir"
        return 1
    fi
}

# Function to set environment variables
set_environment() {
    local environment=$1
    
    print_status "Setting up environment: $environment"
    
    case $environment in
        "qa")
            export SAMAY_FRONTEND_URL="http://localhost:3001/login"
            print_status "Frontend URL: http://localhost:3001/login"
            ;;
        "prod")
            export SAMAY_FRONTEND_URL="https://getsamay.vercel.app/login"
            print_status "Frontend URL: https://getsamay.vercel.app/login"
            ;;
        *)
            print_error "Unknown environment: $environment"
            show_usage
            exit 1
            ;;
    esac
}

# Function to run a single test
run_test() {
    local test_file=$1
    local test_name=$(basename "$test_file")
    
    print_status "Running $test_name..."
    echo "----------------------------------------"
    
    if [ ! -f "$test_file" ]; then
        print_error "Test file not found: $test_file"
        return 1
    fi
    
    # Run the test and capture output
    if python3 "$test_file"; then
        print_success "$test_name passed"
        return 0
    else
        print_error "$test_name failed"
        return 1
    fi
}

# Function to run all tests
run_all_tests() {
    local environment=$1
    local tests_dir="$(dirname "$0")"
    local passed=0
    local total=0
    
    print_status "Starting test suite for environment: $environment"
    echo ""
    
    # Set environment variables
    set_environment "$environment"
    echo ""
    
    # Find all Python test files
    for test_file in "$tests_dir"/*.py; do
        if [ -f "$test_file" ]; then
            total=$((total + 1))
            if run_test "$test_file"; then
                passed=$((passed + 1))
            fi
            echo ""
        fi
    done
    
    # Print summary
    echo "========================================"
    print_status "Test Summary: $passed/$total tests passed"
    
    if [ $passed -eq $total ]; then
        print_success "🎉 All tests passed!"
        print_success "Environment: $environment"
        print_success "Frontend URL: $SAMAY_FRONTEND_URL"
        return 0
    else
        print_error "❌ Some tests failed"
        return 1
    fi
}

# Main function
main() {
    local environment=${1:-"prod"}
    
    # Handle special options
    case $environment in
        --help|-h)
            show_usage
            exit 0
            ;;
        --list-tests)
            list_tests
            exit 0
            ;;
    esac
    
    # Validate environment
    case $environment in
        qa|prod)
            ;;
        *)
            print_error "Unknown environment: $environment"
            show_usage
            exit 1
            ;;
    esac
    
    print_status "Samay Core Engine Test Runner"
    print_status "Environment: $environment"
    echo ""
    
    # Run all tests
    if run_all_tests "$environment"; then
        exit 0
    else
        exit 1
    fi
}

# Run main function with all arguments
main "$@"

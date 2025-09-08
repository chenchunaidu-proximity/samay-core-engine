#!/bin/bash
# Run all Samay Sync tests.
# This script runs all tests in the correct order and provides a comprehensive test report.

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SAMAY_SYNC_DIR="$(dirname "$SCRIPT_DIR")"

# Change to samay-sync directory
cd "$SAMAY_SYNC_DIR"

# Function to run a test file
run_test() {
    local test_file="$1"
    local test_name="$2"
    
    echo -e "\n${CYAN}🧪 Running $test_name...${NC}"
    echo "============================================================"
    
    if [ ! -f "tests/$test_file" ]; then
        echo -e "${RED}⚠️ Test file not found: tests/$test_file${NC}"
        return 1
    fi
    
    # Run the test and capture output
    if python3 "tests/$test_file" 2>&1; then
        echo -e "${GREEN}✅ $test_name PASSED${NC}"
        return 0
    else
        echo -e "${RED}❌ $test_name FAILED${NC}"
        return 1
    fi
}

# Function to print summary
print_summary() {
    local passed="$1"
    local total="$2"
    local start_time="$3"
    local end_time="$4"
    
    local duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "0.00")
    local success_rate=$(echo "scale=1; $passed * 100 / $total" | bc -l 2>/dev/null || echo "0.0")
    
    echo -e "\n============================================================"
    echo -e "${BLUE}📊 TEST SUMMARY${NC}"
    echo -e "============================================================"
    echo -e "Total Tests: $total"
    echo -e "Passed: ${GREEN}$passed${NC}"
    echo -e "Failed: ${RED}$((total - passed))${NC}"
    echo -e "Success Rate: ${GREEN}${success_rate}%${NC}"
    echo -e "Total Time: ${YELLOW}${duration}s${NC}"
    
    echo -e "\n${PURPLE}💡 RECOMMENDATIONS:${NC}"
    if [ "$passed" -eq "$total" ]; then
        echo -e "${GREEN}🎉 All tests passed! The system is ready for production.${NC}"
        echo -e "${GREEN}✅ Ready for Team F and Team B integration.${NC}"
    else
        echo -e "${YELLOW}⚠️ Some tests failed. Please review the errors above.${NC}"
        echo -e "${YELLOW}🔧 Fix the failing tests before proceeding to the next step.${NC}"
    fi
}

# Main execution
echo -e "${BLUE}🚀 Samay Sync - Running All Tests${NC}"
echo -e "============================================================"

# Record start time
start_time=$(date +%s.%N)

# Define test files in order of dependency
declare -a test_files=(
    "test_config.py:Configuration Module Tests"
    "test_database.py:Database Module Tests"
    "test_state_manager.py:Sync State Manager Tests"
    "test_oauth_manager.py:OAuth Manager Tests"
    "test_sync_manager.py:Sync Manager Tests"
    "test_tray_integration.py:Tray Integration Tests"
    "test_integration.py:Dashboard Integration Tests"
)

# Track results
passed=0
total=${#test_files[@]}

# Run each test
for test_entry in "${test_files[@]}"; do
    IFS=':' read -r test_file test_name <<< "$test_entry"
    
    if run_test "$test_file" "$test_name"; then
        ((passed++))
    fi
done

# Record end time
end_time=$(date +%s.%N)

# Print summary
print_summary "$passed" "$total" "$start_time" "$end_time"

# Exit with appropriate code
if [ "$passed" -eq "$total" ]; then
    exit 0
else
    exit 1
fi
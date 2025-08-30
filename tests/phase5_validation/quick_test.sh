#!/bin/bash
# Phase 5 Validation Quick Test Script for Linux/Mac
# Runs all tests and generates analysis report

echo "========================================"
echo "Phase 5 Validation Test Suite"
echo "========================================"
echo

# Check Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create directories if they don't exist
mkdir -p results reports

# Run all tests
echo "Running all 5 test scenarios..."
echo "----------------------------------------"
python3 run_tests.py --all --verbose

if [ $? -ne 0 ]; then
    echo
    echo "Error: Test execution failed"
    exit 1
fi

echo
echo "========================================"
echo "Analyzing test results..."
echo "========================================"
python3 analyze_results.py --summary --format all

echo
echo "========================================"
echo "Test execution complete!"
echo "========================================"
echo
echo "Results saved in: results/"
echo "Reports saved in: reports/"
echo

# Open the latest HTML report if it exists (Mac)
if [[ "$OSTYPE" == "darwin"* ]]; then
    latest_report=$(ls -t reports/analysis_report_*.html 2>/dev/null | head -1)
    if [ -n "$latest_report" ]; then
        echo "Opening HTML report..."
        open "$latest_report"
    fi
# Linux with xdg-open
elif command -v xdg-open &> /dev/null; then
    latest_report=$(ls -t reports/analysis_report_*.html 2>/dev/null | head -1)
    if [ -n "$latest_report" ]; then
        echo "Opening HTML report..."
        xdg-open "$latest_report"
    fi
fi
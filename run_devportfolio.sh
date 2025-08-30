#!/bin/bash

echo "========================================"
echo "Starting DevPortfolio Project Execution"
echo "========================================"
echo

# Create timestamp for unique folder
timestamp=$(date +"%Y%m%d_%H%M%S")

# Set project name
project_name="DevPortfolio"

# Create output directory path
output_dir="projects/${project_name}_${timestamp}"

echo "Project will be created in: $output_dir"
echo

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "WARNING: ANTHROPIC_API_KEY not set. Will run in mock mode."
    echo "To use real API, set: export ANTHROPIC_API_KEY=your-key-here"
    echo
fi

echo "Starting agent swarm execution..."
echo "========================================"
echo

# Run the orchestrator with all fixes applied
python orchestrate_enhanced.py \
    --project-type=full_stack_api \
    --requirements=requirements_devportfolio.yaml \
    --output-dir="$output_dir" \
    --progress \
    --max-parallel=2 \
    --verbose

exit_code=$?

echo
echo "========================================"
if [ $exit_code -eq 0 ]; then
    echo "SUCCESS: Project generated in $output_dir"
    echo
    echo "You can find your project files at:"
    echo "  $(pwd)/$output_dir"
else
    echo "ERROR: Execution failed. Check the logs above for details."
fi
echo "========================================"
# Project Isolation Fix - Timestamped Output Directories

## Problem Solved
Previously, the agent swarm would write all files to hardcoded directories like `/project/` or `devportfolio/`, causing:
- Conflicts between multiple executions
- Files overwriting each other
- Confusion about which files belong to which run
- Path errors when directories didn't exist

## Solution Implemented

### 1. Timestamped Project Directories
Each execution now creates a unique timestamped folder:
```
projects/
├── DevPortfolio_20250830_173000/  # First run
├── DevPortfolio_20250830_174500/  # Second run
└── DevPortfolio_20250830_180000/  # Third run
```

### 2. Context-Aware File Writing
The `write_file_tool` now:
- Gets the project directory from the AgentContext
- Handles all path styles correctly:
  - `/project/file.py` → `projects/DevPortfolio_TIMESTAMP/file.py`
  - `/absolute/path.py` → `projects/DevPortfolio_TIMESTAMP/absolute/path.py`
  - `relative/file.py` → `projects/DevPortfolio_TIMESTAMP/relative/file.py`

### 3. Command Line Options
New `--output-dir` parameter allows manual control:
```bash
# Auto-generated timestamped folder (recommended)
python orchestrate_enhanced.py --project-type=full_stack_api --requirements=requirements_devportfolio.yaml

# Custom output directory
python orchestrate_enhanced.py --project-type=full_stack_api --requirements=requirements_devportfolio.yaml --output-dir="my_custom_folder"
```

## Files Modified

1. **orchestrate_enhanced.py**
   - Added `output_dir` parameter to `execute_enhanced_workflow()`
   - Creates timestamped directories automatically
   - Passes project directory through context

2. **lib/agent_runtime.py**
   - Modified `write_file_tool()` to use project directory from context
   - Better path handling for Windows/Linux compatibility
   - All files now go into the isolated project directory

## Usage Instructions

### Easy Method (Recommended)

**For Windows:**
```batch
run_devportfolio.bat
```

**For Mac/Linux:**
```bash
chmod +x run_devportfolio.sh
./run_devportfolio.sh
```

### Manual Method
```bash
python orchestrate_enhanced.py \
    --project-type=full_stack_api \
    --requirements=requirements_devportfolio.yaml \
    --progress \
    --max-parallel=2
```

### With Custom Directory
```bash
python orchestrate_enhanced.py \
    --project-type=full_stack_api \
    --requirements=requirements_devportfolio.yaml \
    --output-dir="projects/my_test_run" \
    --progress
```

## Benefits

1. **No Conflicts**: Each run is completely isolated
2. **Easy Comparison**: Compare outputs from different runs
3. **Clean Testing**: Delete a single folder to clean up a test run
4. **Better Organization**: All project files in one place
5. **Debugging**: Easy to see what each execution produced

## Project Structure Example

After running, you'll get:
```
projects/DevPortfolio_20250830_173000/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Docker services
├── database.py            # Database setup
├── routers/              # API routes
│   ├── portfolio.py
│   ├── blog.py
│   ├── auth.py
│   └── analytics.py
├── models/               # Data models
│   ├── user.py
│   ├── portfolio.py
│   └── blog.py
├── services/             # Business logic
│   ├── ai_service.py    # OpenAI integration
│   └── github_service.py
├── utils/                # Utilities
│   ├── security.py
│   └── logger.py
├── frontend/             # React application
│   ├── package.json
│   ├── src/
│   └── public/
└── tests/                # Test files
    ├── test_api.py
    └── test_models.py
```

## Verification

To verify the fix is working:
1. Run the workflow twice
2. Check that two different folders are created
3. Verify files don't overwrite between runs
4. Confirm all files are in the project folder, not scattered

## Troubleshooting

If you still see files in wrong locations:
1. Make sure you're using the updated `orchestrate_enhanced.py`
2. Verify the agent_runtime.py has the new write_file_tool
3. Check that context includes "project_directory" in artifacts

## API Key Setup

For real execution (not mock):
```bash
# Windows
set ANTHROPIC_API_KEY=your-api-key-here

# Mac/Linux
export ANTHROPIC_API_KEY=your-api-key-here
```

Without an API key, it will run in mock mode (for testing).
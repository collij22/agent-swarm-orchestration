# Phase 5 Validation Test Suite

Comprehensive testing framework for validating all 5 phases of the agent swarm system upgrades.

## 📋 Overview

This test suite validates the complete production-grade agent swarm system, testing all improvements from Phases 1-5:

- **Phase 1**: Core Integration (requirement tracking, validation)
- **Phase 2**: Production Infrastructure (monitoring, recovery)
- **Phase 3**: Quality Assurance (benchmarks, quality gates)
- **Phase 4**: Advanced Features (ML orchestration, self-healing)
- **Phase 5**: Production Readiness (security, caching, optimization)

## 🎯 Test Scenarios

### 1. E-Commerce Platform MVP (`ecommerce`)
- **Focus**: Full-stack development, payment integration
- **Agents**: 8 agents including frontend, backend, database
- **Complexity**: Medium
- **Key Features**: User auth, shopping cart, payment processing, admin panel

### 2. Real-Time Analytics Dashboard (`analytics`)
- **Focus**: AI integration, performance optimization
- **Agents**: 7 agents with heavy AI specialist usage
- **Complexity**: Medium
- **Key Features**: Real-time data, AI predictions, WebSocket updates, caching

### 3. Microservices Migration (`microservices`)
- **Focus**: Legacy migration, DevOps, containerization
- **Agents**: 8 agents including code migrator and DevOps
- **Complexity**: Medium-High
- **Key Features**: Service decomposition, Docker, Kubernetes, CI/CD

### 4. Mobile-First Social App (`mobile`)
- **Focus**: Frontend specialist, mobile optimization
- **Agents**: 7 agents with frontend focus
- **Complexity**: Medium
- **Key Features**: Real-time chat, media upload, push notifications, PWA

### 5. AI-Powered Content CMS (`ai_cms`)
- **Focus**: AI specialist enhanced features
- **Agents**: 8 agents with AI-heavy workflow
- **Complexity**: Medium
- **Key Features**: Content generation, caching, fallback chains, rate limiting

## 🚀 Quick Start

### Run All Tests (Recommended)
```bash
# Windows
quick_test.bat

# Linux/Mac
chmod +x quick_test.sh
./quick_test.sh
```

This will:
1. Run all 5 test scenarios
2. Generate analysis reports
3. Open HTML report automatically

### Run Individual Tests
```bash
# Run specific test
python run_tests.py --test ecommerce

# Run multiple tests
python run_tests.py --test ecommerce analytics mobile

# List available tests
python run_tests.py --list
```

### Run Tests in Parallel
```bash
# Run all tests in parallel (faster but more resource intensive)
python run_tests.py --all --parallel
```

## 📊 Analyzing Results

### Generate Analysis Report
```bash
# Analyze latest results
python analyze_results.py

# Analyze specific results file
python analyze_results.py --file results/test_results_20241219_120000.json

# Generate specific format
python analyze_results.py --format html
python analyze_results.py --format markdown
python analyze_results.py --format json

# Print summary to console
python analyze_results.py --summary
```

### Report Types

1. **HTML Report**: Interactive report with charts and tables
2. **Markdown Report**: Detailed text report for documentation
3. **JSON Report**: Machine-readable format for integration

## 🔧 Configuration

### Test Configuration (`test_config.yaml`)

Key settings:
- **Mock Mode**: Enhanced mock with 5% failure rate for resilience testing
- **Logging**: Detailed human-readable logs enabled
- **Benchmarks**: Quality threshold at 80%, requirement coverage at 85%
- **Execution**: Sequential by default, can run parallel

### Customizing Tests

1. **Modify Requirements**: Edit files in `requirements/` directory
2. **Adjust Configuration**: Update `test_config.yaml`
3. **Change Failure Rates**: Modify `mock_mode.failure_rates` in config

## 📁 Directory Structure

```
phase5_validation/
├── requirements/           # Test scenario requirement files
│   ├── ecommerce_platform.yaml
│   ├── analytics_dashboard.yaml
│   ├── microservices_migration.yaml
│   ├── social_mobile_app.yaml
│   └── ai_content_cms.yaml
├── results/               # Test execution results (auto-created)
├── reports/               # Analysis reports (auto-created)
├── run_tests.py          # Main test runner
├── analyze_results.py    # Results analyzer
├── test_config.yaml      # Test configuration
├── quick_test.bat        # Windows quick start
├── quick_test.sh         # Linux/Mac quick start
└── README.md            # This file
```

## 📈 Success Metrics

Tests are evaluated on:

1. **Quality Score** (0-100%):
   - Success: 30 points
   - Agent execution: 20 points
   - Files created: 15 points
   - Requirement completion: 25 points
   - Time bonus: 10 points
   - Error/warning penalties

2. **Phase Validation**:
   - Phase 1: Requirement tracking active
   - Phase 2: Error recovery working (<20% error rate)
   - Phase 3: Quality scores >70%
   - Phase 4: Multiple agents orchestrated (>5 per test)
   - Phase 5: Overall success rate >80%

3. **Performance Benchmarks**:
   - Execution time <300s per test
   - Memory usage <512MB
   - CPU usage <80%

## 🔍 Viewing Session Logs

Human-readable logs are saved in the main sessions directory:

```bash
# View latest human-readable log
type ..\..\sessions\session_*_human.md  # Windows
cat ../../sessions/session_*_human.md   # Linux/Mac

# View JSON session data
python ../../session_cli.py list
python ../../session_cli.py view <session_id>
```

## 🐛 Troubleshooting

### Common Issues

1. **"No test result files found"**
   - Run tests first: `python run_tests.py --all`

2. **"Python is not installed"**
   - Ensure Python 3.8+ is installed and in PATH

3. **"Module not found" errors**
   - Install dependencies: `pip install pyyaml`

4. **Tests timing out**
   - Increase timeout in `test_config.yaml`
   - Run tests sequentially instead of parallel

5. **Low quality scores**
   - Check error patterns in analysis report
   - Review agent execution in human-readable logs
   - Verify requirement files are properly formatted

### Debug Mode

```bash
# Run with verbose output
python run_tests.py --all --verbose

# Check specific test configuration
python -c "import yaml; print(yaml.safe_load(open('requirements/ecommerce_platform.yaml')))"
```

## 📊 Expected Results

With the fully upgraded system, you should see:

- **Success Rate**: 85-95% (with 5% controlled failures)
- **Average Quality Score**: 85-95%
- **All 5 Phases Validated**: ✓
- **15 Agents Utilized**: Across all tests
- **Execution Time**: 2-3 minutes per test in mock mode

## 🎯 Next Steps

After running tests:

1. **Review HTML Report**: Check overall performance and phase validation
2. **Analyze Failures**: Look at error patterns in the report
3. **Check Human Logs**: Review `sessions/*_human.md` for detailed execution
4. **Compare Results**: Track improvements over multiple test runs
5. **Run with Real API**: Remove `--mode mock` for production testing

## 📝 Notes

- Tests use **enhanced mock mode** by default (no API costs)
- Human-readable logs are automatically generated
- Results are preserved for historical comparison
- All tests validate Phase 1-5 improvements
- Configuration supports both Windows and Linux/Mac

---

*Last Updated: December 2024*
*System Version: 100% Complete (All 5 Phases)*
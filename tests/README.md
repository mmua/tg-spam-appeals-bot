# Appeals Bot Smoke Tests

This directory contains comprehensive smoke tests for the F1News Appeals Bot to ensure all core functionality works correctly.

## Test Structure

```
tests/
├── conftest.py           # Test configuration and fixtures
├── test_database.py      # Database layer smoke tests  
├── test_handlers.py      # Bot handlers smoke tests
├── test_utils.py         # Utility functions smoke tests
├── test_integration.py   # End-to-end workflow tests
├── run_smoke_tests.py    # Test runner script
└── README.md            # This file
```

## What These Tests Cover

### 🗄️ Database Tests (`test_database.py`)
- Database initialization
- Appeal creation and retrieval
- Status updates 
- Statistics calculation
- User isolation
- Data integrity

### 🤖 Handler Tests (`test_handlers.py`) 
- All bot commands (`/start`, `/help`, `/appeal`, `/status`)
- Admin commands (`/approve`, `/reject`, `/info`)
- Russian message translations
- Error handling
- Admin-only restrictions

### 🔧 Utils Tests (`test_utils.py`)
- Text validation
- User mention formatting
- Unban service integration

### 🔄 Integration Tests (`test_integration.py`)
- Complete appeal workflows (submit → approve/reject → notify)
- Multi-user scenarios
- State transitions
- Permission checks
- Error recovery

## Running the Tests

### Quick Smoke Test (Recommended)
```bash
# Run all smoke tests
python tests/run_smoke_tests.py
```

### Individual Test Categories
```bash
# Database tests only
pytest tests/test_database.py -v

# Handler tests only  
pytest tests/test_handlers.py -v

# Integration tests only
pytest tests/test_integration.py -v

# Utils tests only
pytest tests/test_utils.py -v
```

### Full Test Suite
```bash
# Run all tests with coverage
pytest tests/ --cov=src/appeals_bot --cov-report=term-missing

# Run with detailed output
pytest tests/ -v --tb=long
```

## Test Features

### ✅ **Comprehensive Coverage**
- Tests all major bot functionality
- Covers happy paths and error cases
- Validates Russian translations
- Tests admin permissions

### 🔒 **Isolated Tests**
- Each test uses temporary database
- No test dependencies
- Clean state for each test
- Mocked external services

### 🚀 **Fast Execution**
- Lightweight smoke tests
- Minimal setup/teardown
- Parallelizable tests
- Quick feedback loop

### 📊 **Clear Output**
- Descriptive test names
- Helpful assertion messages
- Detailed failure reporting
- Progress indicators

## Test Dependencies

Tests automatically use:
- **Temporary SQLite databases** - No impact on real data
- **Mocked Telegram API** - No actual messages sent
- **Mocked external services** - No network calls
- **Test fixtures** - Consistent test data

## Expected Results

When everything works correctly:
```
🔥 Running Appeals Bot Smoke Tests...
==================================================

🧪 Running Database Tests...
✅ Database Tests PASSED

🧪 Running Handlers Tests...
✅ Handlers Tests PASSED

🧪 Running Utils Tests...
✅ Utils Tests PASSED

🧪 Running Integration Tests...
✅ Integration Tests PASSED

==================================================
✅ All smoke tests passed!
```

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Install in development mode
pip install -e .
```

**Database Permission Errors**
```bash
# Ensure write permissions in temp directory
chmod 755 tests/
```

**Missing Dependencies**
```bash
# Install test dependencies
pip install -e .[test]
```

### Adding New Tests

1. Follow naming convention: `test_*.py`
2. Use descriptive test method names
3. Add docstrings explaining what's being tested
4. Use appropriate fixtures from `conftest.py`
5. Test both success and failure cases

### Test Philosophy

These are **smoke tests** - they verify that core functionality works without being exhaustive unit tests. They're designed to:

- ✅ Catch major regressions quickly
- ✅ Validate deployments 
- ✅ Ensure core workflows function
- ❌ Not replace comprehensive unit/integration testing
- ❌ Not test every edge case
- ❌ Not validate performance characteristics
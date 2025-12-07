# LLM Load Testing Tool

Comprehensive load testing tool for LLM endpoints with web-based configuration UI.

## Features

✅ **Web UI for Configuration** - Easy-to-use browser interface
✅ **Automatic Retries** - Exponential backoff for failed requests
✅ **SSL Flexibility** - Option to disable SSL verification for testing
✅ **Health Monitoring** - Continuous endpoint health checks
✅ **Response Validation** - Captures actual LLM responses
✅ **Detailed Metrics** - Response times, throughput, success rates
✅ **MCP & Agentic Workloads** - Realistic test scenarios
✅ **Configurable Context Lengths** - Test with varying token counts

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start Web UI

```bash
python3 web_ui.py
```

Then open your browser to: **http://localhost:5000**

### 3. Configure & Run Test

- Enter your endpoint URL, model name, and API key (if needed)
- Choose a preset (Quick, Standard, or Stress test)
- Or customize all parameters
- Click "Start Test"
- Watch real-time output

## Key Improvements in This Version

### Fixed Issues from Previous Version

1. **Automatic Retry Logic** - Requests that fail or timeout are automatically retried with exponential backoff
2. **Better Error Handling** - Distinguishes between client errors (4xx) and server errors (5xx)
3. **Reduced Context Sizes** - Smaller prompts reduce the chance of timeouts
4. **Staggered Start** - Users don't all start at once (avoids thundering herd)
5. **SSL Flexibility** - Can disable SSL verification for testing environments
6. **Shorter Max Tokens** - Reduced from 2048 to 500 for faster responses
7. **Better Connection Pooling** - Optimized for concurrent requests

### Web UI Features

- **Preset Configurations**:
  - Quick Test: 10 users, 1 minute
  - Standard Test: 60 users, 5 minutes
  - Stress Test: 120 users, 10 minutes

- **Real-time Monitoring**:
  - Live output streaming
  - Test duration counter
  - Start/stop controls

- **Configuration Management**:
  - Save/load configurations
  - All parameters editable
  - Validation built-in

## Command Line Usage

If you prefer command line:

### Using Config File

1. Create `test_config.json`:
```json
{
  "endpoint": "https://your-endpoint.com",
  "model_name": "your-model",
  "api_key": "your-key-or-empty",
  "concurrent_users": 60,
  "test_duration_seconds": 300,
  "max_context_tokens": 6000,
  "request_timeout": 60,
  "max_retries": 2,
  "verify_ssl": false
}
```

2. Run the test:
```bash
python3 load-test-llm.py
```

### Using Default Config

Just run:
```bash
python3 load-test-llm.py
```

It will use the defaults defined in the script.

## Understanding the Output

### Console Output

```
[User 001] MCP_file_search | Context: 1K tokens | Status: success | Time: 17.91s | Response: To find all Python files...
[User 010] MCP_file_search | Context: 1K tokens | Status: error | Time: 31.25s
  [Retry 1/2] User 010: HTTP 503: Service Unavailable
[User 010] MCP_file_search | Context: 1K tokens | Status: success (retry 1) | Time: 3.45s | Response: Based on the file structure...

[HEALTH CHECK ✓] Endpoint is ALIVE (Elapsed: 30s, Active requests: 42)
```

### Final Statistics

```
Total Requests: 150
Successful: 142 (94.7%)
Failed: 5 (3.3%)
Timeouts: 3 (2.0%)
Retried requests: 28 (18.7%)

Response Time Statistics:
  Min: 2.13s
  Max: 35.42s
  Mean: 12.34s
  Median: 10.12s
  P95: 24.56s
  P99: 32.11s
```

## Troubleshooting

### High Failure Rate

**Problem**: Many requests failing with errors or timeouts

**Solutions**:
- Reduce `concurrent_users` (try 30 instead of 60)
- Increase `request_timeout` (try 90 or 120 seconds)
- Reduce `max_context_tokens` (try 3000 instead of 6000)
- Check if your endpoint has rate limiting

### Slow Responses

**Problem**: All requests taking 30+ seconds

**Solutions**:
- Your endpoint may be overloaded
- Try reducing concurrent users
- Check endpoint resource limits (GPU/CPU/memory)
- Verify model is properly loaded

### SSL Certificate Errors

**Problem**: SSL verification failures

**Solutions**:
- Set `verify_ssl: false` in config (for testing only!)
- Or fix SSL certificates on your endpoint

### Connection Refused

**Problem**: Cannot connect to endpoint

**Solutions**:
- Verify the endpoint URL is correct
- Check network connectivity
- Verify API key is valid
- Check if endpoint requires VPN/firewall access

## Configuration Parameters

| Parameter | Description | Default | Range |
|-----------|-------------|---------|-------|
| `endpoint` | LLM API endpoint URL | - | - |
| `model_name` | Model identifier | - | - |
| `api_key` | Bearer token (optional) | "" | - |
| `concurrent_users` | Simultaneous users | 60 | 1-500 |
| `test_duration_seconds` | Test duration | 300 | 10-3600 |
| `max_context_tokens` | Max context length | 6000 | 1000-200000 |
| `request_timeout` | Timeout per request | 60 | 10-300 |
| `max_retries` | Retry attempts | 2 | 0-5 |
| `verify_ssl` | SSL verification | false | true/false |

## Test Scenarios

The script simulates two types of workloads:

### MCP (Model Context Protocol) Scenarios
- **File Search** (~30% of max context): Searching and reading files
- **Data Analysis** (~50% of max context): Database queries and statistics
- **Code Review** (~40% of max context): Security and performance analysis

### Agentic AI Scenarios
- **Research Tasks** (~60% of max context): Multi-source information gathering
- **Planning Tasks** (~70% of max context): Architecture planning
- **Problem Solving** (~80% of max context): Log analysis and debugging

## Output Files

After each test run:

- **JSON Results**: `load_test_results_YYYYMMDD_HHMMSS.json`
  - Complete test data
  - All request details
  - Health check timeline
  - Response samples

## Web UI Screenshots

The web UI provides:

1. **Configuration Form** - All parameters in one place
2. **Preset Buttons** - Quick test selection
3. **Real-time Output** - Live test progress
4. **Status Indicator** - Running/Idle with timer
5. **Control Buttons** - Start/Stop/Save

## Security Notes

- API keys are stored in `test_config.json` - keep this file secure
- SSL verification disabled by default for testing - enable in production
- Web UI runs on localhost only by default
- No authentication on web UI - don't expose to untrusted networks

## Advanced Usage

### Custom Test Scenarios

Edit the `MCP_PROMPTS` or `AGENTIC_PROMPTS` arrays in `load-test-llm.py` to add your own scenarios.

### Integration with CI/CD

Run tests programmatically:

```bash
# Create config
cat > test_config.json << EOF
{
  "endpoint": "$ENDPOINT_URL",
  "model_name": "$MODEL_NAME",
  "api_key": "$API_KEY",
  "concurrent_users": 30,
  "test_duration_seconds": 60
}
EOF

# Run test
python3 load-test-llm.py

# Check results
python3 -c "
import json
with open(max(glob.glob('load_test_results_*.json'))) as f:
    data = json.load(f)
    success_rate = data['summary']['successful'] / data['summary']['total_requests']
    assert success_rate > 0.95, f'Success rate too low: {success_rate}'
"
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the output logs
3. Check the JSON results file for detailed error information

## License

This tool is provided as-is for load testing purposes.

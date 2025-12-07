# LLM Load Testing Script

This script simulates 120 concurrent users making requests to your LLM endpoint with MCP (Model Context Protocol) and Agentic AI workloads.

## Features

- **120 Concurrent Users**: Simulates real-world load with concurrent requests
- **MCP Workloads**: File search, data analysis, code review scenarios
- **Agentic AI Workloads**: Research, planning, problem-solving, multi-agent collaboration
- **Variable Context Lengths**: Tests from 30% to 90% of 128K context window (38K - 115K tokens)
- **Endpoint Health Monitoring**: Automated health checks every 30 seconds to ensure endpoint stays alive
- **Response Validation**: Captures and saves actual LLM responses to verify endpoint functionality
- **Comprehensive Metrics**: Response times, throughput, success rates, token usage
- **Detailed Reporting**: JSON output with all request details, response samples, and health check timeline

## Installation

```bash
pip install -r load-test-requirements.txt
```

## Usage

### Basic Run (5 minutes, 120 users)

```bash
python load-test-llm.py
```

### Customize Configuration

Edit the `TestConfig` class in the script:

```python
@dataclass
class TestConfig:
    endpoint: str = "https://granite-3-2-8b-instruct-predictor-maas-apicast-production.apps.maas.redhatworkshops.io:443"
    api_key: str = "c9b374de984142d6f91ae3baf101ab3d"
    model_name: str = "granite-3-2-8b-instruct"
    concurrent_users: int = 120  # Change this
    test_duration_seconds: int = 300  # Change this (300 = 5 minutes)
    max_context_tokens: int = 128000
```

### Run Longer Test (30 minutes)

Change `test_duration_seconds` to `1800` in the script, or run from command line:

```bash
# Edit the script to change test_duration_seconds to 1800
python load-test-llm.py
```

## Test Scenarios

### MCP Scenarios (Tool Use)
1. **File Search** (~38K tokens): Simulates searching files and reading code
2. **Data Analysis** (~64K tokens): Database queries and statistical analysis
3. **Code Review** (~51K tokens): Security and performance analysis

### Agentic AI Scenarios (Multi-step Reasoning)
1. **Research Task** (~77K tokens): Multi-source information gathering
2. **Planning Task** (~90K tokens): Complex architecture planning
3. **Problem Solving** (~102K tokens): Log analysis and debugging
4. **Multi-Agent Collaboration** (~115K tokens): Coordinating multiple AI agents

## Output

### Console Output
Real-time progress for each request with response snippets:
```
Performing initial health check...
✓ Initial health check PASSED - endpoint is responsive

[User 042] MCP_file_search | Context: 38K tokens | Status: success | Time: 2.45s | Response: Based on the file structure provided, I can help you search for Python files...
[User 089] Agentic_planning_task | Context: 87K tokens | Status: success | Time: 8.32s | Response: I'll break down this e-commerce architecture design into a comprehensive plan...

[HEALTH CHECK ✓] Endpoint is ALIVE (Elapsed: 30s)

[User 015] Agentic_problem_solving | Context: 95K tokens | Status: success | Time: 12.10s | Response: Let me analyze these distributed system failures systematically...
```

### Summary Statistics
- Total requests and success rate
- Response time statistics (min, max, mean, median, P95, P99)
- Token usage (sent and received)
- Breakdown by request type
- Context length distribution
- Error analysis
- Throughput metrics
- **Endpoint Health Timeline**: Shows all health checks throughout the test
- **Sample Responses**: First 10 successful responses with actual content

### JSON Output File
Detailed results saved to: `load_test_results_YYYYMMDD_HHMMSS.json`

```json
{
  "config": {...},
  "summary": {
    "total_requests": 450,
    "successful": 445,
    "failed": 3,
    "timeouts": 2,
    "endpoint_health": {
      "total_checks": 10,
      "healthy_checks": 10,
      "final_status": "healthy"
    }
  },
  "health_checks": [
    {
      "timestamp": 1234567890.123,
      "status": "healthy",
      "http_status": 200,
      "response": "OK"
    }
  ],
  "response_samples": [
    {
      "user_id": 5,
      "request_type": "MCP_file_search",
      "timestamp": 1234567890.456,
      "response": "Based on your request, I found..."
    }
  ],
  "results": [
    {
      "user_id": 0,
      "request_type": "Agentic_planning_task",
      "response_content": "I'll help you design...",
      "timestamp": 1234567890.789,
      ...
    }
  ]
}
```

## Interpreting Results

### Success Criteria
- **Success Rate**: Should be >95% for production readiness
- **P95 Response Time**: Should be <10s for good user experience
- **P99 Response Time**: Should be <20s for acceptable experience
- **Health Checks**: All health checks should pass (endpoint stays alive)
- **Response Quality**: Sample responses should contain coherent, relevant content
- **No Timeouts**: Indicates system stability

### Performance Benchmarks
- **Low Context (0-32K)**: Expected 2-5s response time
- **Medium Context (32-64K)**: Expected 5-10s response time
- **High Context (64-96K)**: Expected 10-15s response time
- **Very High Context (96-128K)**: Expected 15-25s response time

### Common Issues
1. **High Timeout Rate**: Increase server resources or reduce concurrent users
2. **Increasing Response Times**: Model may be throttling, check rate limits
3. **HTTP 429 Errors**: Rate limiting active, adjust request frequency
4. **HTTP 503 Errors**: Service overloaded, scale up infrastructure
5. **Failed Health Checks**: Endpoint becoming unresponsive under load - check resource limits
6. **Empty Responses**: Check response samples to verify endpoint is generating actual content

## Advanced Usage

### Adjust User Behavior

Modify the `simulate_user` method to change:
- **Think time**: `await asyncio.sleep(random.uniform(2, 8))` (currently 2-8 seconds)
- **MCP vs Agentic ratio**: `is_mcp = random.random() < 0.5` (currently 50/50)

### Add Custom Scenarios

Add new prompts to `MCP_PROMPTS` or `AGENTIC_PROMPTS`:

```python
{
    "name": "custom_scenario",
    "context_multiplier": 0.5,  # 50% of max context
    "prompt": """Your custom prompt here with {placeholders}""",
    "placeholders": "data to fill in"
}
```

### Monitor System Resources

While the test runs, monitor:
- GPU utilization: `nvidia-smi -l 1`
- Pod metrics: `kubectl top pods -n llm`
- Request queue: Check your model server logs

## Troubleshooting

### SSL/TLS Errors
If you encounter SSL verification errors, you can disable verification (not recommended for production):

Add to the session creation:
```python
async with aiohttp.ClientSession(connector=connector, timeout=timeout, connector_owner=False) as session:
```

### Connection Limits
If you hit connection limits, reduce `concurrent_users` or adjust the connector:
```python
connector = aiohttp.TCPConnector(limit=200, limit_per_host=150)
```

### Memory Issues
For very long tests, results list can grow large. Consider writing results incrementally to disk.

## Example Results

```
================================================================================
Load Test Results
================================================================================

Total Requests: 482
Successful: 468 (97.1%)
Failed: 12 (2.5%)
Timeouts: 2 (0.4%)

Response Time Statistics:
  Min: 1.23s
  Max: 24.56s
  Mean: 7.89s
  Median: 6.45s
  P95: 15.32s
  P99: 21.87s

Token Statistics:
  Avg Context Length: 65,432 tokens
  Avg Response Length: 1,845 tokens
  Total Tokens Sent: 30,622,176
  Total Tokens Received: 863,460

Throughput:
  Requests/second: 1.61
  Successful requests/second: 1.56
```

## License

This script is provided as-is for load testing purposes.

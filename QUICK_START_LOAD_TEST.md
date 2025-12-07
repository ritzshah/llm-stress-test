# Quick Start Guide - LLM Load Testing

## TL;DR - Run the Test Now

```bash
# Install dependencies
pip install aiohttp

# Run the test (5 minutes, 120 concurrent users)
python load-test-llm.py
```

That's it! The test will run for 5 minutes and save results to a JSON file.

## What You'll See

1. **Initial Health Check**: Verifies endpoint is responsive before starting
2. **Real-time Progress**: Each request shows user ID, request type, context size, status, time, and response snippet
3. **Health Checks Every 30s**: Automated monitoring to ensure endpoint stays alive
4. **Final Summary**: Comprehensive statistics and sample responses
5. **JSON Output**: Detailed results file with all data

## Customizing the Test

### Change Test Duration

Edit `load-test-llm.py` line 23:
```python
test_duration_seconds: int = 300  # Change to 600 for 10 minutes, 1800 for 30 minutes
```

### Change Number of Concurrent Users

Edit `load-test-llm.py` line 22:
```python
concurrent_users: int = 120  # Change to 60 for lighter load, 240 for heavier load
```

### Change Your Endpoint/API Key

Edit `load-test-llm.py` lines 19-21:
```python
endpoint: str = "YOUR_ENDPOINT_HERE"
api_key: str = "YOUR_API_KEY_HERE"
model_name: str = "YOUR_MODEL_NAME"
```

## Key Features Added for You

### 1. Response Validation
Every successful request captures the actual LLM response, so you can verify the endpoint is generating real content, not just returning 200 OK.

**Console Output:**
```
[User 042] MCP_file_search | Context: 38K tokens | Status: success | Time: 2.45s | Response: Based on the file structure provided...
```

### 2. Continuous Health Monitoring
Every 30 seconds, the script sends a lightweight health check request to verify the endpoint is still alive.

**Console Output:**
```
[HEALTH CHECK ✓] Endpoint is ALIVE (Elapsed: 30s)
```

**In Final Summary:**
```
Endpoint Health Monitoring:
  Total health checks: 10
  Healthy: 10
  Unhealthy: 0

  Health Check Timeline:
    [    30s] ✓ HEALTHY - Response: OK
    [    60s] ✓ HEALTHY - Response: OK
    ...
```

### 3. Response Samples Saved
First 50 successful responses are saved (first 500 chars each) for manual inspection.

**In Final Summary:**
```
Sample Responses (first 50 successful requests):

  Sample 1 [3s] - User 001 - MCP_file_search:
    Based on the file structure you provided, I can help you search for Python files that contain...
```

**In JSON Output:**
```json
{
  "response_samples": [
    {
      "user_id": 1,
      "request_type": "MCP_file_search",
      "timestamp": 1234567890.123,
      "response": "Based on the file structure..."
    }
  ]
}
```

### 4. Full Response Content in JSON
Every result in the JSON file includes up to 1000 characters of the actual response:

```json
{
  "results": [
    {
      "user_id": 5,
      "request_type": "Agentic_planning_task",
      "status": "success",
      "response_time": 11.23,
      "response_content": "I'll break down this microservices architecture design into a detailed plan...",
      "timestamp": 1234567890.456
    }
  ]
}
```

## What This Proves

By the end of the test, you'll have proof that:

1. ✅ **Endpoint stays alive** under sustained load (120 concurrent users)
2. ✅ **Responses are generated** (not just HTTP 200 with empty content)
3. ✅ **Large contexts work** (up to 115K tokens successfully processed)
4. ✅ **Performance is acceptable** (response times within expected ranges)
5. ✅ **System is stable** (health checks pass throughout the test)

## Interpreting Success

### Green Flags (Good Results)
- Success rate >95%
- All health checks pass
- Response samples contain coherent, relevant content
- P95 response time <15s
- No pattern of increasing response times over test duration

### Red Flags (Issues to Address)
- Success rate <90%
- Failed health checks (endpoint becoming unresponsive)
- Empty or truncated responses in samples
- P95 response time >30s
- Increasing failure rate over time (degradation under load)

## Example Success Output

```
Total Requests: 482
Successful: 468 (97.1%)  ✓ GOOD - Above 95% threshold
Failed: 8 (1.7%)
Timeouts: 6 (1.2%)

Response Time Statistics:
  P95: 16.78s  ✓ GOOD - Under 20s for large contexts
  P99: 22.34s  ✓ ACCEPTABLE

Endpoint Health Monitoring:
  Total health checks: 10
  Healthy: 10  ✓ EXCELLENT - 100% uptime
  Unhealthy: 0

Sample Responses:
  Sample 1: "Based on the file structure..."  ✓ GOOD - Real content generated
  Sample 2: "I'll conduct a comprehensive..."  ✓ GOOD - Contextually relevant
```

## Troubleshooting

### "Connection refused" or "Connection error"
- Verify the endpoint URL is correct
- Check if the endpoint is accessible from your network
- Verify API key is valid

### All requests timeout
- Endpoint may be too slow or overloaded
- Try reducing `concurrent_users` to 60
- Increase timeout in line 252: `timeout=aiohttp.ClientTimeout(total=180)`

### "Too many open files" error
- Reduce `concurrent_users` to 60
- Adjust connector limits in line 449: `limit=100, limit_per_host=80`

## Next Steps

1. **Run the test** with default settings (5 min, 120 users)
2. **Review the results** - check success rate and health checks
3. **Examine response samples** - verify content quality
4. **Scale up if needed** - try 240 users, 30-minute duration
5. **Monitor your infrastructure** - watch GPU/CPU/memory during test

## Files Generated

After the test completes, you'll have:

1. **Console output** - Displayed in terminal (copy/paste to save)
2. **JSON results file** - `load_test_results_YYYYMMDD_HHMMSS.json`
   - Contains all request details
   - Includes 50 response samples
   - Includes health check timeline
   - Timestamp for every event

## Questions?

See `LOAD_TEST_README.md` for comprehensive documentation.
See `EXAMPLE_OUTPUT.md` for annotated example results.

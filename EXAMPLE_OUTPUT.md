# Example Load Test Output

## Console Output During Test

```
================================================================================
Starting LLM Load Test
================================================================================
Endpoint: https://granite-3-2-8b-instruct-predictor-maas-apicast-production.apps.maas.redhatworkshops.io:443
Model: granite-3-2-8b-instruct
Concurrent Users: 120
Test Duration: 300 seconds
Max Context: 128K tokens
================================================================================

Performing initial health check...
✓ Initial health check PASSED - endpoint is responsive

[User 001] MCP_file_search | Context: 32K tokens | Status: success | Time: 3.21s | Response: Based on the file structure you provided, I can help you search for Python files...
[User 002] Agentic_research_task | Context: 68K tokens | Status: success | Time: 7.89s | Response: I'll conduct a comprehensive research analysis on AI's impact on software development...
[User 003] MCP_data_analysis | Context: 58K tokens | Status: success | Time: 6.45s | Response: Let me analyze the sales trends from your database schema. First, I'll execute...
[User 004] Agentic_planning_task | Context: 87K tokens | Status: success | Time: 11.23s | Response: I'll break down this microservices architecture design into a detailed plan...

[HEALTH CHECK ✓] Endpoint is ALIVE (Elapsed: 30s)

[User 005] MCP_code_review | Context: 45K tokens | Status: success | Time: 5.67s | Response: I've reviewed the code files you provided. Here are the security vulnerabilities...
[User 006] Agentic_problem_solving | Context: 95K tokens | Status: success | Time: 13.45s | Response: Let me systematically analyze these distributed system failures using chain-of...
...

[HEALTH CHECK ✓] Endpoint is ALIVE (Elapsed: 60s)
[HEALTH CHECK ✓] Endpoint is ALIVE (Elapsed: 90s)
...
```

## Final Results Summary

```
================================================================================
Load Test Results
================================================================================

Total Requests: 482
Successful: 468 (97.1%)
Failed: 8 (1.7%)
Timeouts: 6 (1.2%)

Response Time Statistics:
  Min: 2.13s
  Max: 24.56s
  Mean: 8.34s
  Median: 7.12s
  P95: 16.78s
  P99: 22.34s

Token Statistics:
  Avg Context Length: 67,432 tokens
  Avg Response Length: 1,247 tokens
  Total Tokens Sent: 31,566,176
  Total Tokens Received: 583,796

Breakdown by Request Type:
  Agentic_multi_agent_collaboration: 81 requests, 78 successful, avg time: 14.23s
  Agentic_planning_task: 79 requests, 77 successful, avg time: 11.89s
  Agentic_problem_solving: 83 requests, 81 successful, avg time: 13.45s
  Agentic_research_task: 78 requests, 76 successful, avg time: 9.67s
  MCP_code_review: 82 requests, 80 successful, avg time: 6.34s
  MCP_data_analysis: 79 requests, 76 successful, avg time: 7.89s
  MCP_file_search: 80 requests, 80 successful, avg time: 4.23s

Context Length Distribution:
  0-32K tokens: 102 requests, avg time: 4.56s
  32-64K tokens: 156 requests, avg time: 8.12s
  64-96K tokens: 128 requests, avg time: 12.34s
  96-128K tokens: 82 requests, avg time: 16.78s

Error Details:
  [5x] Request timeout
  [2x] HTTP 503: Service Temporarily Unavailable
  [1x] HTTP 500: Internal Server Error

Throughput:
  Requests/second: 1.61
  Successful requests/second: 1.56

Endpoint Health Monitoring:
  Total health checks: 10
  Healthy: 10
  Unhealthy: 0

  Health Check Timeline:
    [    30s] ✓ HEALTHY - Response: OK
    [    60s] ✓ HEALTHY - Response: OK
    [    90s] ✓ HEALTHY - Response: OK
    [   120s] ✓ HEALTHY - Response: OK
    [   150s] ✓ HEALTHY - Response: OK
    [   180s] ✓ HEALTHY - Response: OK
    [   210s] ✓ HEALTHY - Response: OK
    [   240s] ✓ HEALTHY - Response: OK
    [   270s] ✓ HEALTHY - Response: OK
    [   300s] ✓ HEALTHY - Response: OK

Sample Responses (first 50 successful requests):

  Sample 1 [3s] - User 001 - MCP_file_search:
    Based on the file structure you provided, I can help you search for Python files that contain database connection logic. Let me analyze the codebase systematically:

    First, I'll use the search_files tool to find files matching database-related patterns:
    - Files containing "connection", "db", "database" in their names
    - Common database libraries like psycopg2, pymongo, sqlalchemy

    After reviewing the file tree, I found several candidate...

  Sample 2 [8s] - User 002 - Agentic_research_task:
    I'll conduct a comprehensive research analysis on AI's impact on software development practices. Let me break this down into systematic subtasks:

    **Phase 1: Information Gathering**
    Based on the research context provided, I've identified several key areas to investigate:
    1. AI-assisted code generation and completion
    2. Automated testing and quality assurance
    3. Code review and security analysis
    4. Project planning and estimation

    **Phase 2: Synthesis**
    Analyzing the 100 previous studies, I observe several recurring themes...

  Sample 3 [6s] - User 003 - MCP_data_analysis:
    Let me analyze the sales trends from your database schema. I'll use the available tools to execute queries and calculate statistics.

    **Step 1: Query Recent Sales Data**
    I'll execute_query to get the last quarter's sales:
    ```sql
    SELECT product_id, SUM(amount) as total_sales, COUNT(*) as transaction_count
    FROM sales
    WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 3 MONTH)
    GROUP BY product_id
    ORDER BY total_sales DESC
    ```

    **Step 2: Identify Top Performers**
    Based on the query results, the top 5 products are...

================================================================================

Detailed results saved to: load_test_results_20251206_143022.json
  - Includes 50 response samples
  - Includes 10 health check results
```

## Key Takeaways from This Example

### ✅ Positive Indicators
- **97.1% Success Rate**: Exceeds the 95% threshold for production readiness
- **All Health Checks Passed**: Endpoint remained responsive throughout entire test
- **Response Quality**: Sample responses show coherent, contextually relevant content
- **Consistent Performance**: Response times correlate with context length as expected

### ⚠️ Areas of Concern
- **P99 Response Time**: 22.34s is acceptable but on the higher end
- **Some Timeouts**: 6 timeouts (1.2%) under heavy load - may need to increase timeout threshold or optimize
- **Occasional 503 Errors**: Suggests brief periods of resource saturation

### 📊 Performance Insights
1. **Context scaling is linear**: Higher context = proportionally higher response time
2. **Agentic tasks take longer**: Multi-agent and problem-solving tasks average 13-14s vs 4-8s for MCP tasks
3. **Throughput is stable**: ~1.6 requests/second sustained over 5 minutes with 120 concurrent users
4. **Model handles large contexts well**: Successfully processing up to 115K token contexts

### 🎯 Recommendations
1. **Production Ready**: System can handle 120+ concurrent users
2. **Consider auto-scaling**: To handle 503 errors during peak load
3. **Monitor health checks**: Current 100% uptime is excellent - maintain this
4. **Optimize timeout settings**: Current 2-minute timeout is appropriate for high-context requests

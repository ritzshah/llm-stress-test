#!/usr/bin/env python3
"""
LLM Load Testing Script for MCP and Agentic AI Workloads
Simulates concurrent users with varying context lengths
"""

import asyncio
import aiohttp
import time
import json
import random
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
import statistics
import sys

@dataclass
class TestConfig:
    endpoint: str = "https://litellm-prod.apps.maas.redhatworkshops.io"
    api_key: str = "sk-7j03l3X2oAB09Ee0FeYMZA"
    model_name: str = "llama-scout-17b"
    concurrent_users: int = 60
    test_duration_seconds: int = 300  # 5 minutes
    max_context_tokens: int = 6000  # 6K context
    request_timeout: int = 60  # Timeout per request in seconds
    max_retries: int = 2  # Number of retries per request
    verify_ssl: bool = False  # Disable SSL verification for testing

@dataclass
class RequestResult:
    user_id: int
    request_type: str
    context_length: int
    status: str
    response_time: float
    tokens_sent: int
    tokens_received: int
    response_content: str = None
    error: str = None
    timestamp: float = None
    retry_count: int = 0


class LLMLoadTester:
    def __init__(self, config: TestConfig):
        self.config = config
        self.results: List[RequestResult] = []
        self.start_time = None
        self.endpoint_alive = True
        self.health_check_results = []
        self.response_samples = []  # Store sample responses
        self.active_requests = 0

    # MCP-style prompts with tool use
    MCP_PROMPTS = [
        {
            "name": "file_search",
            "context_multiplier": 0.3,  # 30% of max context
            "prompt": """You are an AI assistant with access to a file system.
The user has asked you to search for files matching a pattern.
Available tools:
- search_files(pattern: str, path: str) -> List[str]
- read_file(path: str) -> str
- list_directory(path: str) -> List[str]

Context: You have access to a large codebase with the following structure:
{file_tree}

User request: Find all Python files that contain database connection logic and summarize their contents.
""",
            "file_tree": "\n".join([f"src/module_{i}/file_{j}.py" for i in range(10) for j in range(5)])
        },
        {
            "name": "data_analysis",
            "context_multiplier": 0.5,  # 50% of max context
            "prompt": """You are a data analysis AI with access to query tools.
Available tools:
- execute_query(sql: str) -> DataFrame
- calculate_statistics(data: List) -> Dict
- create_visualization(data: List, chart_type: str) -> Image

Context: Database schema and sample data:
{schema_data}

User request: Analyze the sales trends over the last quarter and identify the top performing products.
""",
            "schema_data": json.dumps({
                "tables": {
                    "sales": {"columns": ["id", "product_id", "amount", "date", "customer_id"] * 10},
                    "products": {"columns": ["id", "name", "category", "price"] * 10},
                    "customers": {"columns": ["id", "name", "email", "region"] * 10}
                },
                "sample_data": [{"record": i, "data": "sample" * 10} for i in range(20)]
            }, indent=2)
        },
        {
            "name": "code_review",
            "context_multiplier": 0.4,
            "prompt": """You are a code review AI assistant.
Available tools:
- analyze_code(file_path: str) -> CodeAnalysis
- check_security(code: str) -> SecurityReport
- suggest_improvements(code: str) -> List[Suggestion]

Context: Review the following code files:
{code_files}

User request: Review these files for security vulnerabilities and performance issues.
""",
            "code_files": "\n\n".join([f"# File: module_{i}.py\n" + "def function():\n    pass\n" * 20 for i in range(5)])
        }
    ]

    # Agentic AI prompts with multi-step reasoning
    AGENTIC_PROMPTS = [
        {
            "name": "research_task",
            "context_multiplier": 0.6,
            "prompt": """You are an autonomous research agent. Your task involves:
1. Gathering information from multiple sources
2. Synthesizing the information
3. Drawing conclusions
4. Providing recommendations

Previous research context:
{research_context}

Current task: Research the impact of AI on software development practices and provide a comprehensive analysis.
Please break this down into subtasks and execute them systematically.
""",
            "research_context": "\n".join([f"Study {i}: " + "Finding " * 30 for i in range(10)])
        },
        {
            "name": "planning_task",
            "context_multiplier": 0.7,
            "prompt": """You are a planning agent responsible for breaking down complex tasks.
You have access to previous planning sessions and outcomes.

Historical planning data:
{planning_history}

Current objective: Design and implement a scalable microservices architecture for an e-commerce platform.
Create a detailed implementation plan with:
- Architecture decisions
- Technology choices
- Implementation steps
- Risk assessment
- Timeline estimates
""",
            "planning_history": json.dumps([{
                "session": i,
                "tasks": ["task" * 10 for _ in range(5)],
                "outcomes": "success" * 20
            } for i in range(5)], indent=2)
        },
        {
            "name": "problem_solving",
            "context_multiplier": 0.8,
            "prompt": """You are a problem-solving agent with reasoning capabilities.
You need to analyze complex scenarios and provide solutions.

Problem context and constraints:
{problem_context}

Problem: A distributed system is experiencing intermittent failures. Analyze the logs, identify root causes, and propose solutions.
Use chain-of-thought reasoning to work through this systematically.
""",
            "problem_context": "\n".join([
                f"Log entry {i}: {json.dumps({'timestamp': i, 'level': 'ERROR', 'message': 'error' * 10, 'stack': 'trace' * 10})}"
                for i in range(15)
            ])
        }
    ]

    def estimate_tokens(self, text: str) -> int:
        """Rough estimate: ~4 characters per token"""
        return len(text) // 4

    def create_prompt(self, prompt_template: Dict, target_tokens: int) -> str:
        """Create a prompt with approximately target_tokens"""
        base_prompt = prompt_template["prompt"]

        # Fill in template variables
        for key in prompt_template.keys():
            if key not in ["name", "context_multiplier", "prompt"]:
                placeholder = "{" + key + "}"
                if placeholder in base_prompt:
                    base_prompt = base_prompt.replace(placeholder, str(prompt_template[key]))

        # Pad to reach target tokens if needed
        current_tokens = self.estimate_tokens(base_prompt)
        if current_tokens < target_tokens:
            padding_needed = (target_tokens - current_tokens) * 4  # chars needed
            padding = "Additional context: " + ("detail " * (padding_needed // 7))
            base_prompt += "\n\n" + padding

        return base_prompt

    async def send_llm_request(
        self,
        session: aiohttp.ClientSession,
        user_id: int,
        prompt: str,
        request_type: str,
        context_length: int
    ) -> RequestResult:
        """Send a single request to the LLM endpoint with retry logic"""

        for retry in range(self.config.max_retries + 1):
            headers = {
                "Content-Type": "application/json"
            }

            # Add Authorization header only if API key is provided
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

            payload = {
                "model": self.config.model_name,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,  # Reduced for faster responses
                "temperature": 0.7
            }

            start_time = time.time()
            self.active_requests += 1

            try:
                async with session.post(
                    f"{self.config.endpoint}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.request_timeout),
                    ssl=self.config.verify_ssl
                ) as response:
                    response_time = time.time() - start_time
                    self.active_requests -= 1

                    if response.status == 200:
                        data = await response.json()
                        tokens_received = data.get("usage", {}).get("completion_tokens", 0)

                        # Extract response content
                        response_content = ""
                        if "choices" in data and len(data["choices"]) > 0:
                            response_content = data["choices"][0].get("message", {}).get("content", "")

                        # Store a sample of responses for verification
                        if len(self.response_samples) < 50:  # Keep first 50 responses
                            self.response_samples.append({
                                "user_id": user_id,
                                "request_type": request_type,
                                "timestamp": time.time(),
                                "response": response_content[:500]  # First 500 chars
                            })

                        return RequestResult(
                            user_id=user_id,
                            request_type=request_type,
                            context_length=context_length,
                            status="success",
                            response_time=response_time,
                            tokens_sent=self.estimate_tokens(prompt),
                            tokens_received=tokens_received,
                            response_content=response_content,
                            timestamp=time.time(),
                            retry_count=retry
                        )
                    else:
                        error_text = await response.text()
                        error_msg = f"HTTP {response.status}: {error_text[:200]}"

                        # Don't retry on client errors (4xx)
                        if 400 <= response.status < 500 and retry == 0:
                            self.active_requests -= 1
                            return RequestResult(
                                user_id=user_id,
                                request_type=request_type,
                                context_length=context_length,
                                status="error",
                                response_time=response_time,
                                tokens_sent=self.estimate_tokens(prompt),
                                tokens_received=0,
                                error=error_msg,
                                timestamp=time.time(),
                                retry_count=retry
                            )

                        # Retry on server errors (5xx)
                        if retry < self.config.max_retries:
                            print(f"  [Retry {retry + 1}/{self.config.max_retries}] User {user_id:03d}: {error_msg}")
                            await asyncio.sleep(2 ** retry)  # Exponential backoff
                            continue

                        self.active_requests -= 1
                        return RequestResult(
                            user_id=user_id,
                            request_type=request_type,
                            context_length=context_length,
                            status="error",
                            response_time=response_time,
                            tokens_sent=self.estimate_tokens(prompt),
                            tokens_received=0,
                            error=error_msg,
                            timestamp=time.time(),
                            retry_count=retry
                        )

            except asyncio.TimeoutError:
                self.active_requests -= 1
                if retry < self.config.max_retries:
                    print(f"  [Retry {retry + 1}/{self.config.max_retries}] User {user_id:03d}: Timeout")
                    await asyncio.sleep(1)
                    continue

                return RequestResult(
                    user_id=user_id,
                    request_type=request_type,
                    context_length=context_length,
                    status="timeout",
                    response_time=time.time() - start_time,
                    tokens_sent=self.estimate_tokens(prompt),
                    tokens_received=0,
                    error="Request timeout",
                    timestamp=time.time(),
                    retry_count=retry
                )
            except Exception as e:
                self.active_requests -= 1
                if retry < self.config.max_retries:
                    print(f"  [Retry {retry + 1}/{self.config.max_retries}] User {user_id:03d}: {str(e)[:100]}")
                    await asyncio.sleep(1)
                    continue

                return RequestResult(
                    user_id=user_id,
                    request_type=request_type,
                    context_length=context_length,
                    status="error",
                    response_time=time.time() - start_time,
                    tokens_sent=self.estimate_tokens(prompt),
                    tokens_received=0,
                    error=str(e)[:200],
                    timestamp=time.time(),
                    retry_count=retry
                )

    async def health_check(self, session: aiohttp.ClientSession) -> bool:
        """Perform a health check on the endpoint"""
        headers = {
            "Content-Type": "application/json"
        }

        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        # Simple health check request
        payload = {
            "model": self.config.model_name,
            "messages": [
                {"role": "user", "content": "Reply with OK if you can read this."}
            ],
            "max_tokens": 10,
            "temperature": 0.0
        }

        try:
            async with session.post(
                f"{self.config.endpoint}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
                ssl=self.config.verify_ssl
            ) as response:
                is_healthy = response.status == 200

                if is_healthy:
                    data = await response.json()
                    response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    response_text = await response.text()

                self.health_check_results.append({
                    "timestamp": time.time(),
                    "status": "healthy" if is_healthy else "unhealthy",
                    "http_status": response.status,
                    "response": response_text[:200]
                })

                return is_healthy

        except Exception as e:
            self.health_check_results.append({
                "timestamp": time.time(),
                "status": "error",
                "error": str(e)[:200]
            })
            return False

    async def endpoint_monitor(self, session: aiohttp.ClientSession):
        """Continuously monitor endpoint health during the test"""
        end_time = self.start_time + self.config.test_duration_seconds
        check_interval = 30  # Check every 30 seconds

        # Small delay before first check
        await asyncio.sleep(2)

        while time.time() < end_time:
            is_alive = await self.health_check(session)
            self.endpoint_alive = is_alive

            elapsed = time.time() - self.start_time
            status_emoji = "✓" if is_alive else "✗"
            print(f"\n[HEALTH CHECK {status_emoji}] Endpoint is {'ALIVE' if is_alive else 'DOWN'} "
                  f"(Elapsed: {elapsed:.0f}s, Active requests: {self.active_requests})\n")

            if not is_alive:
                print("WARNING: Endpoint health check failed! Continuing test to gather failure data...")

            await asyncio.sleep(check_interval)

    async def simulate_user(self, session: aiohttp.ClientSession, user_id: int):
        """Simulate a single user's requests throughout the test duration"""
        end_time = self.start_time + self.config.test_duration_seconds

        # Stagger initial requests to avoid thundering herd
        await asyncio.sleep(random.uniform(0, 5))

        while time.time() < end_time:
            # Randomly choose between MCP and Agentic workflow
            is_mcp = random.random() < 0.5

            if is_mcp:
                prompt_template = random.choice(self.MCP_PROMPTS)
                request_type = f"MCP_{prompt_template['name']}"
            else:
                prompt_template = random.choice(self.AGENTIC_PROMPTS)
                request_type = f"Agentic_{prompt_template['name']}"

            # Vary context length based on template and some randomness
            base_context = int(self.config.max_context_tokens * prompt_template['context_multiplier'])
            variation = random.uniform(0.7, 1.0)  # 70-100% of base
            target_tokens = int(base_context * variation)

            # Create prompt
            prompt = self.create_prompt(prompt_template, target_tokens)

            # Send request
            result = await self.send_llm_request(
                session, user_id, prompt, request_type, target_tokens
            )
            self.results.append(result)

            # Print progress with response snippet
            response_snippet = ""
            if result.response_content:
                response_snippet = f" | Response: {result.response_content[:80]}..."

            retry_info = f" (retry {result.retry_count})" if result.retry_count > 0 else ""

            print(f"[User {user_id:03d}] {request_type} | "
                  f"Context: {target_tokens//1000}K tokens | "
                  f"Status: {result.status}{retry_info} | "
                  f"Time: {result.response_time:.2f}s{response_snippet}")

            # Wait before next request (simulate thinking time)
            await asyncio.sleep(random.uniform(2, 8))

    async def run_load_test(self):
        """Run the complete load test"""
        print(f"\n{'='*80}")
        print(f"Starting LLM Load Test")
        print(f"{'='*80}")
        print(f"Endpoint: {self.config.endpoint}")
        print(f"Model: {self.config.model_name}")
        print(f"Concurrent Users: {self.config.concurrent_users}")
        print(f"Test Duration: {self.config.test_duration_seconds} seconds")
        print(f"Max Context: {self.config.max_context_tokens//1000}K tokens")
        print(f"Request Timeout: {self.config.request_timeout}s")
        print(f"Max Retries: {self.config.max_retries}")
        print(f"{'='*80}\n")

        self.start_time = time.time()

        # Create aiohttp session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrent_users + 10,
            limit_per_host=self.config.concurrent_users + 10,
            ttl_dns_cache=300
        )
        timeout = aiohttp.ClientTimeout(total=None)

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Perform initial health check
            print("Performing initial health check...")
            initial_health = await self.health_check(session)
            if initial_health:
                print("✓ Initial health check PASSED - endpoint is responsive\n")
            else:
                print("✗ Initial health check FAILED - endpoint may not be available\n")
                print("Continuing anyway to gather data...\n")

            # Create tasks for all users + health monitor
            user_tasks = [
                self.simulate_user(session, user_id)
                for user_id in range(self.config.concurrent_users)
            ]

            # Add health monitoring task
            monitor_task = self.endpoint_monitor(session)

            # Run all users concurrently with health monitoring
            await asyncio.gather(monitor_task, *user_tasks, return_exceptions=True)

        self.print_results()

    def print_results(self):
        """Print comprehensive test results"""
        print(f"\n{'='*80}")
        print(f"Load Test Results")
        print(f"{'='*80}\n")

        total_requests = len(self.results)
        if total_requests == 0:
            print("No requests completed!")
            return

        successful = [r for r in self.results if r.status == "success"]
        failed = [r for r in self.results if r.status == "error"]
        timeouts = [r for r in self.results if r.status == "timeout"]

        print(f"Total Requests: {total_requests}")
        print(f"Successful: {len(successful)} ({len(successful)/total_requests*100:.1f}%)")
        print(f"Failed: {len(failed)} ({len(failed)/total_requests*100:.1f}%)")
        print(f"Timeouts: {len(timeouts)} ({len(timeouts)/total_requests*100:.1f}%)")

        # Retry statistics
        retried = [r for r in self.results if r.retry_count > 0]
        if retried:
            print(f"Retried requests: {len(retried)} ({len(retried)/total_requests*100:.1f}%)")

        if successful:
            response_times = [r.response_time for r in successful]
            print(f"\nResponse Time Statistics:")
            print(f"  Min: {min(response_times):.2f}s")
            print(f"  Max: {max(response_times):.2f}s")
            print(f"  Mean: {statistics.mean(response_times):.2f}s")
            print(f"  Median: {statistics.median(response_times):.2f}s")
            if len(response_times) > 1:
                print(f"  P95: {sorted(response_times)[int(len(response_times)*0.95)]:.2f}s")
                print(f"  P99: {sorted(response_times)[int(len(response_times)*0.99)]:.2f}s")

            tokens_sent = [r.tokens_sent for r in successful]
            tokens_received = [r.tokens_received for r in successful]
            print(f"\nToken Statistics:")
            print(f"  Avg Context Length: {statistics.mean(tokens_sent):.0f} tokens")
            if sum(tokens_received) > 0:
                print(f"  Avg Response Length: {statistics.mean(tokens_received):.0f} tokens")
            print(f"  Total Tokens Sent: {sum(tokens_sent):,}")
            print(f"  Total Tokens Received: {sum(tokens_received):,}")

        # Breakdown by request type
        print(f"\nBreakdown by Request Type:")
        request_types = {}
        for result in self.results:
            if result.request_type not in request_types:
                request_types[result.request_type] = []
            request_types[result.request_type].append(result)

        for req_type, results in sorted(request_types.items()):
            successful_type = [r for r in results if r.status == "success"]
            avg_time = statistics.mean([r.response_time for r in successful_type]) if successful_type else 0
            print(f"  {req_type}: {len(results)} requests, "
                  f"{len(successful_type)} successful, "
                  f"avg time: {avg_time:.2f}s")

        # Error analysis
        if failed or timeouts:
            print(f"\nError Details:")
            error_counts = {}
            for result in failed + timeouts:
                error_key = result.error[:100] if result.error else "Unknown"
                error_counts[error_key] = error_counts.get(error_key, 0) + 1

            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  [{count}x] {error}")

        # Throughput
        test_duration = time.time() - self.start_time
        print(f"\nThroughput:")
        print(f"  Requests/second: {total_requests/test_duration:.2f}")
        print(f"  Successful requests/second: {len(successful)/test_duration:.2f}")

        # Health check summary
        print(f"\nEndpoint Health Monitoring:")
        healthy_checks = [h for h in self.health_check_results if h.get("status") == "healthy"]
        print(f"  Total health checks: {len(self.health_check_results)}")
        print(f"  Healthy: {len(healthy_checks)}")
        print(f"  Unhealthy: {len(self.health_check_results) - len(healthy_checks)}")

        if self.health_check_results and len(self.health_check_results) <= 20:
            print(f"\n  Health Check Timeline:")
            for check in self.health_check_results:
                elapsed = check['timestamp'] - self.start_time
                status = check.get('status', 'unknown')
                if status == "healthy":
                    response_preview = check.get('response', '')[:50]
                    print(f"    [{elapsed:6.0f}s] ✓ HEALTHY - Response: {response_preview}")
                else:
                    error = check.get('error', check.get('response', 'Unknown error'))[:100]
                    print(f"    [{elapsed:6.0f}s] ✗ UNHEALTHY - {error}")

        # Sample responses
        if self.response_samples:
            print(f"\nSample Responses (first {min(len(self.response_samples), 5)} successful requests):")
            for i, sample in enumerate(self.response_samples[:5], 1):
                elapsed = sample['timestamp'] - self.start_time
                print(f"\n  Sample {i} [{elapsed:.0f}s] - User {sample['user_id']:03d} - {sample['request_type']}:")
                print(f"    {sample['response'][:300]}...")

        print(f"\n{'='*80}\n")

        # Save detailed results to JSON
        output_file = f"load_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "config": {
                    "endpoint": self.config.endpoint,
                    "model": self.config.model_name,
                    "concurrent_users": self.config.concurrent_users,
                    "test_duration": self.config.test_duration_seconds,
                    "max_context": self.config.max_context_tokens,
                    "request_timeout": self.config.request_timeout,
                    "max_retries": self.config.max_retries
                },
                "summary": {
                    "total_requests": total_requests,
                    "successful": len(successful),
                    "failed": len(failed),
                    "timeouts": len(timeouts),
                    "retried": len(retried) if retried else 0,
                    "test_duration": test_duration,
                    "endpoint_health": {
                        "total_checks": len(self.health_check_results),
                        "healthy_checks": len(healthy_checks),
                        "final_status": "healthy" if self.endpoint_alive else "unhealthy"
                    }
                },
                "health_checks": self.health_check_results,
                "response_samples": self.response_samples,
                "results": [
                    {
                        "user_id": r.user_id,
                        "request_type": r.request_type,
                        "context_length": r.context_length,
                        "status": r.status,
                        "response_time": r.response_time,
                        "tokens_sent": r.tokens_sent,
                        "tokens_received": r.tokens_received,
                        "response_content": r.response_content[:1000] if r.response_content else None,
                        "timestamp": r.timestamp,
                        "retry_count": r.retry_count,
                        "error": r.error
                    }
                    for r in self.results
                ]
            }, f, indent=2)

        print(f"Detailed results saved to: {output_file}")
        print(f"  - Includes {len(self.response_samples)} response samples")
        print(f"  - Includes {len(self.health_check_results)} health check results")


def load_config_from_file(config_file: str = "test_config.json") -> Optional[TestConfig]:
    """Load configuration from JSON file"""
    try:
        with open(config_file, 'r') as f:
            data = json.load(f)
            return TestConfig(**data)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading config: {e}")
        return None


async def main():
    # Try to load config from file first
    config = load_config_from_file()

    if config is None:
        # Use default config
        config = TestConfig()

    print(f"Using configuration:")
    print(f"  Endpoint: {config.endpoint}")
    print(f"  Model: {config.model_name}")
    print(f"  Users: {config.concurrent_users}")
    print(f"  Duration: {config.test_duration_seconds}s")

    tester = LLMLoadTester(config)
    await tester.run_load_test()


if __name__ == "__main__":
    asyncio.run(main())

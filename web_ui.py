#!/usr/bin/env python3
"""
Web UI for LLM Load Testing Configuration
Simple Flask-based interface to configure and run load tests
"""

from flask import Flask, render_template_string, request, jsonify, send_file
import json
import subprocess
import os
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Store test status
test_status = {
    "running": False,
    "start_time": None,
    "process": None,
    "output": [],
    "config": None
}

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>LLM Load Test Configuration</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }

        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }

        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }

        .form-group {
            margin-bottom: 25px;
        }

        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
            font-size: 14px;
        }

        .help-text {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }

        input[type="text"],
        input[type="number"],
        input[type="password"] {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e1e8ed;
            border-radius: 8px;
            font-size: 14px;
            transition: all 0.3s;
        }

        input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .checkbox-group {
            display: flex;
            align-items: center;
            gap: 10px;
        }

        input[type="checkbox"] {
            width: 20px;
            height: 20px;
            cursor: pointer;
        }

        .button-group {
            display: flex;
            gap: 15px;
            margin-top: 30px;
        }

        button {
            flex: 1;
            padding: 14px 24px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }

        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }

        .btn-secondary {
            background: #e1e8ed;
            color: #333;
        }

        .btn-secondary:hover:not(:disabled) {
            background: #cbd6e0;
        }

        .btn-danger {
            background: #dc3545;
            color: white;
        }

        .btn-danger:hover:not(:disabled) {
            background: #c82333;
        }

        button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .status-box {
            margin-top: 30px;
            padding: 20px;
            border-radius: 8px;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
        }

        .status-running {
            border-left-color: #28a745;
            background: #d4edda;
        }

        .status-idle {
            border-left-color: #6c757d;
        }

        .output-box {
            margin-top: 20px;
            padding: 20px;
            background: #1e1e1e;
            border-radius: 8px;
            color: #d4d4d4;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }

        .preset-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-bottom: 30px;
        }

        .preset-btn {
            padding: 12px;
            background: #f8f9fa;
            border: 2px solid #e1e8ed;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            text-align: left;
        }

        .preset-btn:hover {
            border-color: #667eea;
            background: #f0f4ff;
        }

        .preset-btn h3 {
            font-size: 14px;
            margin-bottom: 4px;
            color: #333;
        }

        .preset-btn p {
            font-size: 12px;
            color: #666;
        }

        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .grid-2 {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        @media (max-width: 768px) {
            .grid-2 {
                grid-template-columns: 1fr;
            }

            .button-group {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 LLM Load Test Configuration</h1>
        <p class="subtitle">Configure and run load tests for your LLM endpoint</p>

        <div class="preset-buttons">
            <div class="preset-btn" onclick="loadPreset('quick')">
                <h3>⚡ Quick Test</h3>
                <p>10 users, 1 min, 6K context</p>
            </div>
            <div class="preset-btn" onclick="loadPreset('standard')">
                <h3>📊 Standard Test</h3>
                <p>60 users, 5 min, 6K context</p>
            </div>
            <div class="preset-btn" onclick="loadPreset('stress')">
                <h3>💪 Stress Test</h3>
                <p>120 users, 10 min, 128K context</p>
            </div>
        </div>

        <form id="configForm">
            <div class="form-group">
                <label for="endpoint">Endpoint URL *</label>
                <input type="text" id="endpoint" name="endpoint" required
                       placeholder="https://your-endpoint.com"
                       value="{{ config.endpoint }}">
                <div class="help-text">The base URL of your LLM API endpoint</div>
            </div>

            <div class="form-group">
                <label for="model_name">Model Name *</label>
                <input type="text" id="model_name" name="model_name" required
                       placeholder="llama-scout-17b"
                       value="{{ config.model_name }}">
                <div class="help-text">The model identifier to use for requests</div>
            </div>

            <div class="form-group">
                <label for="api_key">API Key (optional)</label>
                <input type="password" id="api_key" name="api_key"
                       placeholder="Leave empty if not required"
                       value="{{ config.api_key }}">
                <div class="help-text">Bearer token for authentication (leave empty if not needed)</div>
            </div>

            <div class="grid-2">
                <div class="form-group">
                    <label for="concurrent_users">Concurrent Users *</label>
                    <input type="number" id="concurrent_users" name="concurrent_users"
                           min="1" max="500" required
                           value="{{ config.concurrent_users }}">
                    <div class="help-text">Number of simultaneous users (1-500)</div>
                </div>

                <div class="form-group">
                    <label for="test_duration_seconds">Duration (seconds) *</label>
                    <input type="number" id="test_duration_seconds" name="test_duration_seconds"
                           min="10" max="3600" required
                           value="{{ config.test_duration_seconds }}">
                    <div class="help-text">Test duration in seconds (10-3600)</div>
                </div>
            </div>

            <div class="grid-2">
                <div class="form-group">
                    <label for="max_context_tokens">Max Context (tokens) *</label>
                    <input type="number" id="max_context_tokens" name="max_context_tokens"
                           min="1000" max="200000" step="1000" required
                           value="{{ config.max_context_tokens }}">
                    <div class="help-text">Maximum context length in tokens</div>
                </div>

                <div class="form-group">
                    <label for="request_timeout">Request Timeout (seconds) *</label>
                    <input type="number" id="request_timeout" name="request_timeout"
                           min="10" max="300" required
                           value="{{ config.request_timeout }}">
                    <div class="help-text">Timeout per request (10-300s)</div>
                </div>
            </div>

            <div class="grid-2">
                <div class="form-group">
                    <label for="max_retries">Max Retries *</label>
                    <input type="number" id="max_retries" name="max_retries"
                           min="0" max="5" required
                           value="{{ config.max_retries }}">
                    <div class="help-text">Number of retry attempts per request</div>
                </div>

                <div class="form-group">
                    <label class="checkbox-group">
                        <input type="checkbox" id="verify_ssl" name="verify_ssl"
                               {{ 'checked' if config.verify_ssl else '' }}>
                        <span>Verify SSL Certificates</span>
                    </label>
                    <div class="help-text">Enable SSL certificate verification</div>
                </div>
            </div>

            <div class="button-group">
                <button type="submit" class="btn-primary" id="startBtn">
                    Start Test
                </button>
                <button type="button" class="btn-secondary" onclick="saveConfig()">
                    Save Config
                </button>
                <button type="button" class="btn-danger" onclick="stopTest()" id="stopBtn" disabled>
                    Stop Test
                </button>
            </div>
        </form>

        <div class="status-box" id="statusBox">
            <strong>Status:</strong> <span id="status">Idle</span>
        </div>

        <div class="output-box" id="outputBox" style="display: none;"></div>
    </div>

    <script>
        let updateInterval = null;

        const presets = {
            quick: {
                concurrent_users: 10,
                test_duration_seconds: 60,
                max_context_tokens: 6000,
                request_timeout: 30,
                max_retries: 1
            },
            standard: {
                concurrent_users: 60,
                test_duration_seconds: 300,
                max_context_tokens: 6000,
                request_timeout: 60,
                max_retries: 2
            },
            stress: {
                concurrent_users: 120,
                test_duration_seconds: 600,
                max_context_tokens: 128000,
                request_timeout: 120,
                max_retries: 3
            }
        };

        function loadPreset(name) {
            const preset = presets[name];
            for (const [key, value] of Object.entries(preset)) {
                const element = document.getElementById(key);
                if (element) {
                    element.value = value;
                }
            }
        }

        document.getElementById('configForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData(e.target);
            const config = {
                endpoint: formData.get('endpoint'),
                model_name: formData.get('model_name'),
                api_key: formData.get('api_key'),
                concurrent_users: parseInt(formData.get('concurrent_users')),
                test_duration_seconds: parseInt(formData.get('test_duration_seconds')),
                max_context_tokens: parseInt(formData.get('max_context_tokens')),
                request_timeout: parseInt(formData.get('request_timeout')),
                max_retries: parseInt(formData.get('max_retries')),
                verify_ssl: formData.get('verify_ssl') === 'on'
            };

            try {
                const response = await fetch('/start_test', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                });

                const result = await response.json();

                if (result.status === 'started') {
                    document.getElementById('startBtn').disabled = true;
                    document.getElementById('stopBtn').disabled = false;
                    document.getElementById('statusBox').className = 'status-box status-running';
                    document.getElementById('outputBox').style.display = 'block';
                    startUpdates();
                } else {
                    alert('Failed to start test: ' + result.message);
                }
            } catch (error) {
                alert('Error starting test: ' + error.message);
            }
        });

        async function stopTest() {
            if (!confirm('Are you sure you want to stop the test?')) {
                return;
            }

            try {
                const response = await fetch('/stop_test', {method: 'POST'});
                const result = await response.json();

                if (result.status === 'stopped') {
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                    document.getElementById('statusBox').className = 'status-box status-idle';
                    stopUpdates();
                }
            } catch (error) {
                alert('Error stopping test: ' + error.message);
            }
        }

        async function saveConfig() {
            const formData = new FormData(document.getElementById('configForm'));
            const config = {
                endpoint: formData.get('endpoint'),
                model_name: formData.get('model_name'),
                api_key: formData.get('api_key'),
                concurrent_users: parseInt(formData.get('concurrent_users')),
                test_duration_seconds: parseInt(formData.get('test_duration_seconds')),
                max_context_tokens: parseInt(formData.get('max_context_tokens')),
                request_timeout: parseInt(formData.get('request_timeout')),
                max_retries: parseInt(formData.get('max_retries')),
                verify_ssl: formData.get('verify_ssl') === 'on'
            };

            try {
                const response = await fetch('/save_config', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                });

                const result = await response.json();
                alert(result.message);
            } catch (error) {
                alert('Error saving config: ' + error.message);
            }
        }

        function startUpdates() {
            updateInterval = setInterval(updateStatus, 1000);
        }

        function stopUpdates() {
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = null;
            }
        }

        async function updateStatus() {
            try {
                const response = await fetch('/status');
                const data = await response.json();

                document.getElementById('status').innerHTML = data.running ?
                    '<span class="spinner"></span> Running (' + formatDuration(data.elapsed) + ')' :
                    'Idle';

                if (data.output && data.output.length > 0) {
                    document.getElementById('outputBox').textContent = data.output.join('');
                    document.getElementById('outputBox').scrollTop = document.getElementById('outputBox').scrollHeight;
                }

                if (data.running === false && updateInterval) {
                    stopUpdates();
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('stopBtn').disabled = true;
                    document.getElementById('statusBox').className = 'status-box status-idle';
                }
            } catch (error) {
                console.error('Error updating status:', error);
            }
        }

        function formatDuration(seconds) {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`;
        }

        // Check status on load
        updateStatus();
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    # Load existing config if available
    config = {
        "endpoint": "https://litellm-prod.apps.maas.redhatworkshops.io",
        "model_name": "llama-scout-17b",
        "api_key": "",
        "concurrent_users": 60,
        "test_duration_seconds": 300,
        "max_context_tokens": 6000,
        "request_timeout": 60,
        "max_retries": 2,
        "verify_ssl": False
    }

    if os.path.exists('test_config.json'):
        try:
            with open('test_config.json', 'r') as f:
                config = json.load(f)
        except:
            pass

    return render_template_string(HTML_TEMPLATE, config=config)


@app.route('/start_test', methods=['POST'])
def start_test():
    global test_status

    if test_status["running"]:
        return jsonify({"status": "error", "message": "Test is already running"})

    config = request.json

    # Save config to file
    with open('test_config.json', 'w') as f:
        json.dump(config, f, indent=2)

    # Start the test in a separate thread
    test_status["running"] = True
    test_status["start_time"] = time.time()
    test_status["output"] = []
    test_status["config"] = config

    thread = threading.Thread(target=run_test)
    thread.daemon = True
    thread.start()

    return jsonify({"status": "started"})


@app.route('/stop_test', methods=['POST'])
def stop_test():
    global test_status

    if test_status["process"]:
        test_status["process"].terminate()
        test_status["process"] = None

    test_status["running"] = False
    test_status["output"].append("\n\n=== Test stopped by user ===\n")

    return jsonify({"status": "stopped"})


@app.route('/status')
def status():
    global test_status

    elapsed = 0
    if test_status["running"] and test_status["start_time"]:
        elapsed = time.time() - test_status["start_time"]

    return jsonify({
        "running": test_status["running"],
        "elapsed": elapsed,
        "output": test_status["output"]
    })


@app.route('/save_config', methods=['POST'])
def save_config():
    config = request.json

    try:
        with open('test_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        return jsonify({"status": "success", "message": "Configuration saved successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


def run_test():
    global test_status

    try:
        # Run the load test script
        process = subprocess.Popen(
            ['python3', 'load-test-llm.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        test_status["process"] = process

        # Stream output
        for line in process.stdout:
            test_status["output"].append(line)

        process.wait()
        test_status["process"] = None
        test_status["running"] = False
        test_status["output"].append("\n\n=== Test completed ===\n")

    except Exception as e:
        test_status["output"].append(f"\n\nError: {str(e)}\n")
        test_status["running"] = False


if __name__ == '__main__':
    print("=" * 80)
    print("LLM Load Test Web UI")
    print("=" * 80)
    print("\nStarting web server...")
    print("Open your browser and navigate to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 80)
    print()

    app.run(host='0.0.0.0', port=5000, debug=False)

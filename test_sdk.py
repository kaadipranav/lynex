import os
import time
from watchllm import WatchLLM

# Initialize SDK
# Use the mock key we defined in auth.py
API_KEY = "sk_test_demo1234567890abcdefghijklmno"
PROJECT_ID = "proj_demo"
HOST = "http://localhost:8000"

client = WatchLLM(api_key=API_KEY, project_id=PROJECT_ID, host=HOST)

print("🚀 Sending test events...")

# 1. Log event
client.capture_log("Hello from Python SDK!", level="info")
print("✅ Log sent")

# 2. Error event
try:
    1 / 0
except Exception as e:
    client.capture_error(e)
    print("✅ Error sent")

# 3. Span event (not implemented in client yet, skipping)
# with client.span("test_operation") as span:
#     time.sleep(0.1)
#     span.set_attribute("custom_attr", "value")
#     print("✅ Span sent")

# 4. Token usage
client.capture_llm_usage(
    model="gpt-3.5-turbo",
    input_tokens=50,
    output_tokens=100,
    cost=0.002
)
print("✅ Usage sent")

# Wait for background worker to flush
print("⏳ Waiting for flush...")
time.sleep(2)
print("🎉 Done!")

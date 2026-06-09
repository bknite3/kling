import requests
import time
import os

API_KEY = os.getenv("sec")
BASE_URL = "https://api.kling.ai/v1" # Or aggregator URL like api.aimlapi.com

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Payload for Text-to-Video (Kling 3.0 Standard)
payload = {
    "model": "kling-v3-text-to-video",
    "prompt": "A cinematic shot of a majestic red panda wearing a tiny wizard hat, reading a glowing spellbook in an ancient library.",
    "aspect_ratio": "16:9",
    "duration": "5",       # Duration in seconds (e.g., 5 or 10)
    "mode": "std"          # 'std' for cost-effective, 'pro' for highest quality
}

# Step 1: Submit the task
response = requests.post(f"{BASE_URL}/videos/generations", json=payload, headers=headers)
task_data = response.json()

# Grab the unique task ID to track progress
task_id = task_data.get("task_id") 
print(f"Task submitted successfully! Task ID: {task_id}")

import requests,time,os,jwt
from dotenv import load_dotenv

load_dotenv()
acc= os.getenv("acc")
sec= os.getenv("sec")

def generate_kling_jwt(acc, sec):
    """Generates the mandatory 3-part JWT token required by Kling"""
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": acc,
        "exp": int(time.time()) + 1800, # Token expires in 30 minutes
        "nbf": int(time.time()) - 5
    }
    # This creates the exact '3-part' token the error message is looking for
    token = jwt.encode(payload, sec, algorithm="HS256", headers=headers)
    return token

# Generate the valid token
tok= generate_kling_jwt(acc,sec)

# BASE_URL = "https://api.kling.ai/v1"
BASE_URL = "https://api-singapore.klingai.com/v1"
headers = {
    "Authorization": f"Bearer {tok}",
    "Content-Type": "application/json"
}

# 1. Change the endpoint from images to videos:
# OLD: f"{BASE_URL}/images/generations"
ENDPOINT = f"{BASE_URL}/videos/image2video"

# 2. Change your payload to the video model format:
payload = {
    "model": "kling-v3-image-to-video", # Video model variant
    "image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb", 
    "prompt": "Animate the background with subtle camera movement.",
    "duration": "5", # Videos require a duration (5 or 10)
    "cfg_scale": 0.5
}

# 3. Post to the video endpoint
response = requests.post(ENDPOINT, json=payload, headers=headers)

import requests, time, os, jwt
from dotenv import load_dotenv

load_dotenv()
acc = os.getenv("acc")
sec = os.getenv("sec")

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
    token = jwt.encode(payload, sec, algorithm="HS256", headers=headers)
    return token

# Define the text file containing your image URLs (one URL per line)
URLS_FILE = "urls.txt"
BASE_URL = "https://api-singapore.klingai.com/v1"
pro = "Change only the shirt of the moving person to a blue gingham check pattern, keeping all other clothing, the person's appearance, actions, and the background completely unchanged"

# --- STEP 1: READ INPUT URLS FROM FILE ---
if not os.path.exists(URLS_FILE):
    print(f"Error: The file '{URLS_FILE}' does not exist. Please create it and add your URLs.")
    exit()

with open(URLS_FILE, "r") as f:
    # Read lines, strip out whitespace/newlines, and skip empty lines
    image_urls = [line.strip() for line in f if line.strip()]

print(f"Loaded {len(image_urls)} image URLs from {URLS_FILE}.\n")

# This variable will store the URL of the first successful shirt generation
first_generated_shirt_url = None

# --- STEP 2: LOOP THROUGH EACH URL ---
for idx, iurl in enumerate(image_urls, start=1):
    print(f"--- Processing Image {idx}/{len(image_urls)}: {iurl} ---")

    # Generate a fresh JWT token per image request to ensure it never expires mid-run
    tok = generate_kling_jwt(acc, sec)
    headers = {
        "Authorization": f"Bearer {tok}",
        "Content-Type": "application/json"
    }

    # Base payload structure
    payload = {
        "model_name": "kling-v3",
        "prompt": pro,
        "image": iurl,
        "aspect_ratio": "16:9",
        "resolution": "2k",
        "n": 1
    }

    # For images after the first one, inject the first generation as a style/clothing reference
    if first_generated_shirt_url:
        print("Applying reference image from the first generation to maintain shirt consistency...")
        payload["ref_image"] = first_generated_shirt_url
        # Optional: Depending on the specific Kling API schema endpoint version,
        # ref_mode can be set to "style" or "character" if supported.
        payload["ref_mode"] = "style"

    # Submit Task
    print("Submitting Image-to-Image request...")
    response = requests.post(f"{BASE_URL}/images/generations", json=payload, headers=headers)

    if response.status_code != 200:
        print(f"Failed to submit image {idx}. Status code: {response.status_code}, Response: {response.text}")
        print("Skipping to next image...\n")
        continue

    response_json = response.json()
    task_id = response_json.get("data", {}).get("task_id")

    if not task_id:
        print(f"Error: Could not retrieve a valid Task ID for image {idx}.")
        print(f"Full Server Response: {response_json}\n")
        continue

    print(f"Task successfully queued! Task ID: {task_id}\n")

    # Polling Loop for the current image
    while True:
        print(f"Checking generation progress for Task {task_id}...")

        status_response = requests.get(f"{BASE_URL}/images/generations/{task_id}", headers=headers)

        try:
            status_json = status_response.json()
        except Exception:
            print("Failed to parse server response, retrying in 5 seconds...")
            time.sleep(5)
            continue

        task_data = status_json.get("data", {})
        status = task_data.get("task_status")

        print(f"Current Status: {status}")

        if status == "succeed":
            task_result = task_data.get("task_result", {})
            result_images = task_result.get("images", [])

            print("\nSuccess! Image transformation complete.")

            # Save each generated variant locally
            for img_idx, img in enumerate(result_images):
                image_url = img.get("url")
                if image_url:
                    # CRITICAL: Capture the very first generated image URL to use as reference for next loops
                    if idx == 1 and first_generated_shirt_url is None:
                        first_generated_shirt_url = image_url
                        print(f"--> Saved reference URL for consistency: {first_generated_shirt_url}")

                    print(f"Downloading image from: {image_url}")

                    if ".jpg" in image_url.lower() or ".jpeg" in image_url.lower():
                        ext = "jpg"
                    else:
                        ext = "png"

                    # Name formats include the line index and variant index to stay organized
                    filename = f"kling_line{idx}_{task_id}_{img_idx}.{ext}"

                    img_response = requests.get(image_url)
                    if img_response.status_code == 200:
                        with open(filename, "wb") as f_img:
                            f_img.write(img_response.content)
                        print(f"Saved successfully as: {filename}")
                    else:
                        print(f"Failed to download image. HTTP Status: {img_response.status_code}")
            print(f"Finished processing image {idx}.\n")
            break

        elif status in ["failed", "cancelled"]:
            print(f"\nTask stopped. Status: {status}. Context: {task_data}\n")
            break

        time.sleep(5)

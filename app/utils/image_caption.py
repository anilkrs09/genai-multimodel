import base64
import requests

def image_to_caption(image_path):
    with open(image_path, "rb") as img_file:
        base64_img = base64.b64encode(img_file.read()).decode("utf-8")
    response = requests.post(
        "http://ollama:11434/api/generate",
        json={"model": "llava:latest", "prompt": "Describe this image.", "images": [base64_img]},
    )
    return response.json()["message"]["content"]

from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import torch
import requests

device = "cuda" if torch.cuda.is_available() else "cpu"
print("DEVICE vision =", device)

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = (
    BlipForConditionalGeneration.from_pretrained(
        "Salesforce/blip-image-captioning-base"
    )
    .to(device)
)

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"


def _call_llm_for_tags(caption: str, limit: int = 3) -> list[str]:
    prompt = (
        "Given the following image caption, produce up to three descriptive single-word tags that capture the main objects or concepts. "
        "Don't worry about using the exact words from the caption—feel free to paraphrase or pick synonymous keywords. "
        "Return the tags as a comma-separated list and avoid filler words.\n\n"
        f"Caption: {caption}"
    )

    payload = {
        "model": "phi3:mini",
        "messages": [{"role": "user", "content": prompt}],
        # "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices") or []
    message = choices[0].get("message") if choices else data.get("message")
    if not message:
        return []

    content = message.get("content", "")
    tags = [tag.strip() for tag in content.replace("\n", ",").split(",") if tag.strip()]
    return tags[:limit]


def describe_image(path):
    image = Image.open(path).convert("RGB")

    inputs = processor(image, return_tensors="pt").to(device)

    out = model.generate(**inputs)

    caption = processor.decode(out[0], skip_special_tokens=True)
    tags = _call_llm_for_tags(caption, limit=5)

    return caption, tags

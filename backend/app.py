import os, io, base64, random, re, json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, ContentSettings, generate_blob_sas, BlobSasPermissions
from openai import AzureOpenAI
from flask_cors import CORS
import requests

load_dotenv()
app = Flask(__name__)
# CORS: allow SPA to call this API from anywhere; supports credentials if ever needed
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# ---------- Azure OpenAI clients ----------
gpt4_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_GPT4_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_GPT4_ENDPOINT"),
)
img_client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_IMAGE_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_IMAGE_ENDPOINT"),
)

GPT4_DEPLOYMENT = os.getenv("GPT4_DEPLOYMENT_NAME")        # e.g. gpt4-deployment
IMG_DEPLOYMENT  = os.getenv("IMAGE_DEPLOYMENT_NAME")       # e.g. gpt-image-1
API_VERSION     = os.getenv("AZURE_OPENAI_API_VERSION")    # 2024-02-15-preview

# ---------- Azure Blob Storage ----------
STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
STORAGE_KEY     = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
CONTAINER       = os.getenv("AZURE_STORAGE_CONTAINER", "generated-images")
PUBLIC_BLOBS    = os.getenv("PUBLIC_BLOBS", "true").lower() == "true"  # default public container

blob_service = BlobServiceClient(
    account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
    credential=STORAGE_KEY
)

def ensure_container():
    try:
        blob_service.create_container(CONTAINER, public_access="blob" if PUBLIC_BLOBS else None)
    except Exception:
        pass  # already exists

def put_blob(name: str, data: bytes, content_type="image/png") -> str:
    ensure_container()
    bc = blob_service.get_blob_client(CONTAINER, name)
    bc.upload_blob(
        data,
        overwrite=True,
        content_settings=ContentSettings(content_type=content_type),
    )
    base = f"https://{STORAGE_ACCOUNT}.blob.core.windows.net/{CONTAINER}/{name}"
    if PUBLIC_BLOBS:
        return base
    # return SAS URL if container is private
    sas = generate_blob_sas(
        account_name=STORAGE_ACCOUNT,
        container_name=CONTAINER,
        blob_name=name,
        account_key=STORAGE_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=24),
    )
    return f"{base}?{sas}"

# ---------- Category prompts (two per category) ----------
CATEGORY_PROMPTS = {
    "Bracelet": [
        """Create a photorealistic, high-end advertisement photograph for HauteCarat, featuring an elegant female model wearing a diamond bracelet. The scene should look like a luxury jewelry campaign photo — soft studio lighting, premium editorial tone, and focus on the bracelet’s craftsmanship.

Jewelry Focus — Bracelet:
- Type: {type}
- Style: {style}
- Metal: {metal}
- Gemstones: {gemstones}
- Stone Size: {stone_size}
- Total Number of Stones: {stone_count}
- Jewelry Width: {width}
- Fit or Length: {fit_length}
- Setting Style: {setting_style}
- Finish: {finish}
- Clasp or Closure: {clasp}
- Accents or Design Elements: {accents}
- Visual Highlights: {highlights}

Aesthetic Tone: Capture HauteCarat’s luxury aesthetic — high-end editorial quality, cinematic lighting, creamy color balance, realistic skin texture, and crystal-clear diamond brilliance. The bracelet should be the hero element, with every gem sharply in focus and soft reflections along the model’s wrist.
""",
        """Create a photorealistic, high-end advertisement photograph for HauteCarat, featuring an elegant female model wearing a stack of luxury diamond bracelets. Sophisticated lighting and a refined background that highlights sparkle and metal contrast.

Jewelry Focus — Bracelets:
- Type: {type}
- Style: {style}
- Metal: {metal}
- Gemstones: {gemstones}
- Stone Size: {stone_size}
- Total Number of Stones: {stone_count}
- Jewelry Width: {width}
- Fit or Length: {fit_length}
- Setting Style: {setting_style}
- Finish: {finish}
- Clasp or Closure: {clasp}
- Accents or Design Elements: {accents}
- Visual Highlights: {highlights}

Aesthetic Tone: Embody HauteCarat’s signature elegance — cinematic warmth, natural texture, jewelry-first focus, realistic skin tone, 4K realism.
"""
    ],
    "Earrings": [
        """Generate a photorealistic on-model image for HauteCarat, featuring a female model wearing the earring shown in the attached image. Ensure realistic proportions, lighting, and wear behavior.

Jewelry Focus — Earrings:
- Type: {type}
- Style: {style}
- Metal: {metal}
- Gemstones: {gemstones}
- Stone Size: {stone_size}
- Total Number of Stones: {stone_count}
- Jewelry Width: {width}
- Fit or Length: {fit_length}
- Setting Style: {setting_style}
- Finish: {finish}
- Clasp or Closure: {clasp}
- Accents or Design Elements: {accents}
- Visual Highlights: {highlights}

Aesthetic: HauteCarat luxury portrait — soft depth-of-field, crystal-clear gemstone detail, realistic skin texture.
""",
        """Generate a 4K ultra-realistic on-model image for HauteCarat, showcasing a female model wearing the earrings depicted in the attached reference image. Replicate the precise design with photorealistic lighting, texture, and wear behavior.

Jewelry Focus — Earrings:
- Type: {type}
- Style: {style}
- Metal: {metal}
- Gemstones: {gemstones}
- Stone Size: {stone_size}
- Total Number of Stones: {stone_count}
- Jewelry Width: {width}
- Fit or Length: {fit_length}
- Setting Style: {setting_style}
- Finish: {finish}
- Clasp or Closure: {clasp}
- Accents or Design Elements: {accents}
- Visual Highlights: {highlights}

Output Goal: Editorial-grade portrait with accurate optical behavior and skin realism.
"""
    ],
    "Rings": [
        """Generate a photorealistic on-model image for HauteCarat, featuring a female model wearing the ring shown in the attached jewelry image. Replicate the design faithfully with soft studio lighting and authentic skin detail.

Jewelry Focus — Ring:
- Type: {type}
- Style: {style}
- Metal: {metal}
- Gemstones: {gemstones}
- Stone Size: {stone_size}
- Total Number of Stones: {stone_count}
- Jewelry Width: {width}
- Fit or Length: {fit_length}
- Setting Style: {setting_style}
- Finish: {finish}
- Clasp or Closure: {clasp}
- Accents or Design Elements: {accents}
- Visual Highlights: {highlights}

Output Goal: 4K photorealistic on-model ring photograph, elegant and brand-consistent.
""",
        """Create a 4K photorealistic on-model image for HauteCarat, featuring a female model wearing the exact ring shown in the attached reference image. Render with lifelike realism and authentic wear characteristics.

Jewelry Focus — Ring:
- Type: {type}
- Style: {style}
- Metal: {metal}
- Gemstones: {gemstones}
- Stone Size: {stone_size}
- Total Number of Stones: {stone_count}
- Jewelry Width: {width}
- Fit or Length: {fit_length}
- Setting Style: {setting_style}
- Finish: {finish}
- Clasp or Closure: {clasp}
- Accents or Design Elements: {accents}
- Visual Highlights: {highlights}

Realism: Proper contact shadows, skin indentation, accurate reflections, natural anatomy.
"""
    ],
    "Necklace": [
        """Generate a 4K photorealistic on-model necklace photograph for HauteCarat, featuring a female model wearing the exact necklace shown in the attached reference image. Replicate the design faithfully with editorial-grade realism.

Jewelry Focus — Necklace:
- Type: {type}
- Style: {style}
- Metal: {metal}
- Gemstones: {gemstones}
- Stone Size: {stone_size}
- Total Number of Stones: {stone_count}
- Jewelry Width: {width}
- Fit or Length: {fit_length}
- Setting Style: {setting_style}
- Finish: {finish}
- Clasp or Closure: {clasp}
- Accents or Design Elements: {accents}
- Visual Highlights: {highlights}

Goal: HauteCarat product gallery quality — soft lighting, accurate optics, natural skin texture.
""",
        """Generate a 4K ultra-realistic on-model image for HauteCarat, featuring a female model wearing the necklace shown in the attached reference image. Reproduce precise gemstone layout, metal tone, and proportions.

Jewelry Focus — Necklace:
- Type: {type}
- Style: {style}
- Metal: {metal}
- Gemstones: {gemstones}
- Stone Size: {stone_size}
- Total Number of Stones: {stone_count}
- Jewelry Width: {width}
- Fit or Length: {fit_length}
- Setting Style: {setting_style}
- Finish: {finish}
- Clasp or Closure: {clasp}
- Accents or Design Elements: {accents}
- Visual Highlights: {highlights}

Output Goal: Cinematic, editorial-quality portrait — accurate drape, contact points, and reflections.
"""
    ]
}

# ---------- helpers ----------
def extract_field(text: str, label: str) -> str:
    m = re.search(rf"{label}\s*:\s*(.+)", text, flags=re.IGNORECASE)
    return m.group(1).strip() if m else ""

def fill_prompt_template(category_prompt: str, description: str, user: dict) -> str:
    return category_prompt.format(
        type=extract_field(description, "Type") or (user.get("category") or ""),
        style=extract_field(description, "Style"),
        metal=extract_field(description, "Metal") or user.get("metal", ""),
        gemstones=extract_field(description, "Gemstones"),
        stone_size=extract_field(description, "Stone Size"),
        stone_count=extract_field(description, "Total Number of Stones"),
        width=extract_field(description, "Jewelry Width") or (f"{user.get('width')} mm" if user.get("width") else ""),
        fit_length=extract_field(description, "Fit or Length") or user.get("fit_length",""),
        setting_style=extract_field(description, "Setting Style"),
        finish=extract_field(description, "Finish"),
        clasp=extract_field(description, "Clasp or Closure"),
        accents=extract_field(description, "Accents or Design Elements"),
        highlights=extract_field(description, "Visual Highlights"),
    )

# ---------- routes ----------
@app.route("/api/healthz", methods=["GET"])
def healthz():
    return jsonify({"ok": True}), 200

@app.route("/api/generate", methods=["POST"])
def generate():
    try:
        category  = (request.form.get("category") or "").strip()
        width     = request.form.get("width")
        fit_len   = request.form.get("fit_length")
        metal     = request.form.get("metal_type")
        files     = request.files.getlist("images")

        if not category or category not in CATEGORY_PROMPTS:
            return jsonify({"message": f"Unsupported or missing category: {category}"}), 400
        if not files:
            return jsonify({"message": "Please upload at least one image"}), 400

        # Take first image as design reference
        ref_file  = files[0]
        ref_bytes = ref_file.read()
        ref_file.seek(0)

        # Store the reference image (optional but helpful)
        ref_name = f"ref_{category.lower()}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{os.urandom(3).hex()}.jpg"
        ref_url  = put_blob(ref_name, ref_bytes, content_type=ref_file.mimetype or "image/jpeg")

        # -------- Phase 1: GPT-4o analysis with image URL context --------
        analysis_prompt = f"""Analyze the attached jewelry image carefully and generate a detailed product description in the HauteCarat structured format.

User-provided details:
- Category: {category}
- Metal: {metal}
- Width: {width} mm
- Fit/Length: {fit_len}

Output fields (labels must match): 
Type, Style, Metal, Gemstones, Stone Size, Total Number of Stones, Jewelry Width, Fit or Length, Setting Style, Finish, Clasp or Closure, Accents or Design Elements, Visual Highlights.
"""
        analysis_messages = [
            {"role": "system", "content": "You are a luxury jewelry catalog AI for HauteCarat."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": analysis_prompt},
                    {"type": "image_url", "image_url": {"url": ref_url}},
                ],
            },
        ]
        analysis = gpt4_client.chat.completions.create(
            model=GPT4_DEPLOYMENT,
            messages=analysis_messages,
            temperature=0.2
        )
        description = analysis.choices[0].message.content

        # -------- Phase 2: gpt-image-1 with reference image (edits), fallback to generate --------
        chosen = random.choice(CATEGORY_PROMPTS[category])
        user_inputs = {"category": category, "width": width, "fit_length": fit_len, "metal": metal}
        final_prompt = fill_prompt_template(chosen, description, user_inputs)

        image_b64 = None
        try:
            # REST: images/edits with multipart form-data (conditions on uploaded image)
            edits_url = f"{os.getenv('AZURE_OPENAI_IMAGE_ENDPOINT').rstrip('/')}/openai/images/edits?api-version={API_VERSION}"
            headers = {"api-key": os.getenv("AZURE_OPENAI_IMAGE_KEY")}
            files_mp = {
                "image": (ref_name, io.BytesIO(ref_bytes), ref_file.mimetype or "image/jpeg"),
            }
            data_mp = {
                "prompt": (
                    "Use the attached jewelry image as the definitive design reference. "
                    "Replicate the exact design faithfully as a photorealistic on-model HauteCarat image. "
                    + final_prompt
                ),
                "n": "1",
                "size": "1024x1024",
                "model": IMG_DEPLOYMENT,  # Azure deployment name
            }
            r = requests.post(edits_url, headers=headers, files=files_mp, data=data_mp, timeout=180)
            r.raise_for_status()
            image_b64 = r.json()["data"][0]["b64_json"]
        except Exception:
            # Fallback to generate (no image conditioning) if edits not available
            gen = img_client.images.generate(
                model=IMG_DEPLOYMENT,
                prompt="Photorealistic on-model HauteCarat jewelry image. Reference design details:\n" + final_prompt,
                size="1024x1024",
                n=1,
            )
            image_b64 = gen.data[0].b64_json

        # Upload output
        image_bytes = base64.b64decode(image_b64)
        out_name = f"generated_{category.lower()}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{os.urandom(3).hex()}.png"
        out_url  = put_blob(out_name, image_bytes, content_type="image/png")

        return jsonify({
            "description": description,   # your UI currently hides this, which is fine
            "image_url": out_url,         # <img> uses this directly; Download button saves it locally
        }), 200

    except Exception as e:
        return jsonify({"message": f"Generation failed: {str(e)}"}), 500


if __name__ == "__main__":
    # Local dev
    app.run(host="0.0.0.0", port=5000)

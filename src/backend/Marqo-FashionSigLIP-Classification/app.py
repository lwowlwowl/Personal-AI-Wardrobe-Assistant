import base64
import contextlib
from io import BytesIO
from typing import Optional

import open_clip
import requests
import torch
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from PIL import Image
from pydantic import BaseModel, Field

# 7-way coarse fashion categories (only classify into these)
# Key stays stable for downstream usage; value used for display/prompting.
CATEGORIES = [
    (
        "upper_body_apparel",
        "上半身服装",
        "tops and upper-body clothing such as t-shirts, shirts, blouses, sweaters, hoodies, bras",
    ),
    (
        "lower_body_apparel",
        "下半身服装",
        "bottoms such as pants, jeans, trousers, leggings, shorts, skirts",
    ),
    (
        "full_body_apparel",
        "连体/裙装",
        "full-body garments such as dresses, gowns, jumpsuits, rompers, overalls",
    ),
    (
        "outerwear",
        "外套类",
        "outerwear such as coats, jackets, parkas, trench coats, blazers, windbreakers",
    ),
    (
        "footwear",
        "鞋类",
        "footwear such as shoes, sneakers, boots, sandals, slippers, heels",
    ),
    (
        "accessories_wearable",
        "所有可穿戴配饰",
        "wearable accessories such as hats, caps, belts, scarves, gloves, sunglasses, jewelry, watches",
    ),
    (
        "bags",
        "包",
        "bags such as handbags, purses, backpacks, tote bags",
    ),
]

class PredictUrlRequest(BaseModel):
    url: str = Field(..., description="Image URL")
    top_k: int = Field(7, ge=1, le=7)


class PredictBase64Request(BaseModel):
    image_base64: str = Field(..., description="Base64-encoded image bytes (no data URI prefix required)")
    top_k: int = Field(7, ge=1, le=7)


class Prediction(BaseModel):
    label: str
    label_zh: str
    score: float


class PredictResponse(BaseModel):
    predicted_label: str
    predicted_label_zh: str
    probabilities: list[Prediction]

MODEL_NAME = "hf-hub:Marqo/marqo-fashionSigLIP"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Lazy-initialized globals (set in startup)
model = None
preprocess_val = None
tokenizer = None
text_features = None

category_ids = [c[0] for c in CATEGORIES]
category_id_to_zh = {c[0]: c[1] for c in CATEGORIES}
category_prompts = [
    # Make the prompt explicit and include examples to help the coarse grouping.
    f"A photo of a fashion item. Category = {cid}. It is {en_desc}."
    for cid, _zh, en_desc in CATEGORIES
]


def _amp_context():
    if DEVICE.type == "cuda":
        return torch.amp.autocast("cuda")
    return contextlib.nullcontext()


def _load_image_from_bytes(data: bytes) -> Image.Image:
    try:
        img = Image.open(BytesIO(data))
        return img.convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"无法解析图片: {e}")


def _load_image_from_url(url: str) -> Image.Image:
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        return _load_image_from_bytes(resp.content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"下载图片失败: {e}")


def _classify_pil_image(image: Image.Image, top_k: int = 7) -> PredictResponse:
    global model, preprocess_val, text_features
    if model is None or preprocess_val is None or text_features is None:
        raise HTTPException(status_code=503, detail="模型尚未初始化完成")

    processed = preprocess_val(image).unsqueeze(0).to(DEVICE)

    with torch.no_grad(), _amp_context():
        image_features = model.encode_image(processed)
        image_features /= image_features.norm(dim=-1, keepdim=True)
        probs = (100 * image_features @ text_features.T).softmax(dim=-1)[0]

    scored = [(category_ids[i], float(probs[i].item())) for i in range(len(category_ids))]
    scored.sort(key=lambda x: x[1], reverse=True)
    scored = scored[:top_k]

    predictions = [
        Prediction(label=cid, label_zh=category_id_to_zh[cid], score=score) for cid, score in scored
    ]
    best = predictions[0]

    return PredictResponse(
        predicted_label=best.label,
        predicted_label_zh=best.label_zh,
        probabilities=predictions,
    )


def _init_model():
    global model, preprocess_val, tokenizer, text_features

    _model, _preprocess_train, _preprocess_val = open_clip.create_model_and_transforms(MODEL_NAME)
    _tokenizer = open_clip.get_tokenizer(MODEL_NAME)

    _model = _model.to(DEVICE)
    _model.eval()

    text = _tokenizer(category_prompts)
    if hasattr(text, "to"):
        text = text.to(DEVICE)

    with torch.no_grad(), _amp_context():
        _text_features = _model.encode_text(text)
        _text_features /= _text_features.norm(dim=-1, keepdim=True)

    model = _model
    preprocess_val = _preprocess_val
    tokenizer = _tokenizer
    text_features = _text_features


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    _init_model()
    yield


app = FastAPI(title="Marqo FashionSigLIP 7-class API", lifespan=lifespan)


@app.get("/health")
def health():
    ready = model is not None and preprocess_val is not None and text_features is not None
    return {"status": "ok" if ready else "loading", "device": str(DEVICE)}


@app.post("/predict", response_model=PredictResponse)
async def predict(
    file: Optional[UploadFile] = File(None, description="上传图片文件（multipart/form-data）"),
    url: Optional[str] = Form(None, description="图片 URL（multipart/form-data）"),
    top_k: int = Form(7, ge=1, le=7, description="返回 top_k（1-7）"),
):
    if file is None and not url:
        raise HTTPException(status_code=400, detail="请上传 file 或提供 url")
    if file is not None and url:
        raise HTTPException(status_code=400, detail="file 和 url 二选一即可")

    if file is not None:
        data = await file.read()
        image = _load_image_from_bytes(data)
    else:
        image = _load_image_from_url(url)  # type: ignore[arg-type]

    return _classify_pil_image(image, top_k=top_k)


@app.post("/predict_url", response_model=PredictResponse)
def predict_url(req: PredictUrlRequest):
    image = _load_image_from_url(req.url)
    return _classify_pil_image(image, top_k=req.top_k)


@app.post("/predict_base64", response_model=PredictResponse)
def predict_base64(req: PredictBase64Request):
    try:
        raw = base64.b64decode(req.image_base64, validate=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"base64 解码失败: {e}")
    image = _load_image_from_bytes(raw)
    return _classify_pil_image(image, top_k=req.top_k)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

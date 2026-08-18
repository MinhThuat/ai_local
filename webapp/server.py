"""
Web app đơn giản gen ảnh Kontext qua LAN.
Nạp N ảnh + 1 lệnh (tiếng Việt) -> N job Kontext riêng -> kết quả hiện lần lượt.

Chạy: python server.py   (mặc định 0.0.0.0:8000)
Cần: ComfyUI đang chạy ở 127.0.0.1:8188 + file workflow_api.json (Save API Format từ ComfyUI).
"""
import copy
import json
import os
import sys

import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response

# ---- Cấu hình (chỉnh ở đây) ----
COMFY = os.environ.get("COMFY_URL", "http://127.0.0.1:8188")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
HERE = os.path.dirname(os.path.abspath(__file__))
WORKFLOW_PATH = os.path.join(HERE, "workflow_api.json")  # bạn export từ ComfyUI
# ép output 2048 nằm trong workflow_api.json (thêm node upscale trước SaveImage).

# ---- Dịch VI -> EN (Argos, CPU, offline) ----
try:
    import argostranslate.translate as _argos
except ImportError:
    _argos = None


def translate_vi_en(text: str) -> str:
    """Dịch tiếng Việt -> Anh. Nếu Argos chưa cài/chưa có gói vi->en thì trả nguyên văn."""
    text = (text or "").strip()
    if not text or _argos is None:
        return text
    try:
        out = _argos.translate(text, "vi", "en")
        return out.strip() or text
    except Exception:
        return text  # thà gửi nguyên văn còn hơn sập


# ---- Nạp workflow template 1 lần ----
def load_workflow():
    if not os.path.exists(WORKFLOW_PATH):
        sys.exit(
            f"THIẾU {WORKFLOW_PATH}\n"
            "Trong ComfyUI: bật Dev mode (Settings) -> Save (API Format) workflow Kontext của bạn,\n"
            "lưu thành webapp/workflow_api.json. Đặt title node prompt (CLIPTextEncode dương) = 'PROMPT'."
        )
    with open(WORKFLOW_PATH, encoding="utf-8") as f:
        return json.load(f)


_BASE_WF = None


def base_workflow():
    global _BASE_WF
    if _BASE_WF is None:
        _BASE_WF = load_workflow()
    return _BASE_WF


def _title(node) -> str:
    return (node.get("_meta", {}) or {}).get("title", "").strip().upper()


def build_job(image_name: str, prompt_en: str) -> dict:
    """Copy workflow, vá node ảnh + node prompt."""
    wf = copy.deepcopy(base_workflow())

    load_image_nodes = [n for n in wf.values() if n.get("class_type") == "LoadImage"]
    if not load_image_nodes:
        raise HTTPException(500, "Workflow không có node LoadImage.")
    for n in load_image_nodes:
        n["inputs"]["image"] = image_name

    encoders = [n for n in wf.values() if n.get("class_type") == "CLIPTextEncode"]
    titled = [n for n in encoders if _title(n) == "PROMPT"]
    targets = titled or (encoders if len(encoders) == 1 else [])
    if not targets:
        raise HTTPException(
            500,
            "Không xác định được node prompt. Đặt title node CLIPTextEncode dương = 'PROMPT'.",
        )
    for n in targets:
        n["inputs"]["text"] = prompt_en
    return wf


# ---- Gọi ComfyUI ----
def comfy_upload(file: UploadFile) -> str:
    r = requests.post(
        f"{COMFY}/upload/image",
        files={"image": (file.filename, file.file, file.content_type or "image/png")},
        data={"overwrite": "false"},
        timeout=60,
    )
    r.raise_for_status()
    j = r.json()
    name = j["name"]
    if j.get("subfolder"):
        name = f"{j['subfolder']}/{name}"
    return name


def comfy_submit(wf: dict) -> str:
    r = requests.post(f"{COMFY}/prompt", json={"prompt": wf}, timeout=60)
    if r.status_code != 200:
        raise HTTPException(502, f"ComfyUI từ chối workflow: {r.text[:400]}")
    return r.json()["prompt_id"]


# ---- App ----
app = FastAPI()


@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "index.html"))


@app.post("/generate")
async def generate(prompt: str = Form(""), images: list[UploadFile] = File(...)):
    if not images:
        raise HTTPException(400, "Cần ít nhất 1 ảnh.")
    try:
        prompt_en = translate_vi_en(prompt)
        jobs = []
        for img in images:
            name = comfy_upload(img)
            wf = build_job(name, prompt_en)
            jobs.append(comfy_submit(wf))
        return {"jobs": jobs, "prompt_en": prompt_en}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()  # in đầy đủ ra cửa sổ server
        raise HTTPException(500, f"{type(e).__name__}: {e}")  # trả gọn về trình duyệt


def _find_output_image(history_entry: dict):
    for out in history_entry.get("outputs", {}).values():
        for im in out.get("images", []):
            if im.get("type") == "output":
                return im
    return None


@app.get("/status/{prompt_id}")
def status(prompt_id: str):
    h = requests.get(f"{COMFY}/history/{prompt_id}", timeout=30).json()
    entry = h.get(prompt_id)
    if entry:
        # history chỉ chứa job đã kết thúc: có ảnh = xong, không có = lỗi.
        if _find_output_image(entry):
            return {"status": "done", "url": f"/result/{prompt_id}"}
        return {"status": "error"}

    # chưa vào history -> tìm trong queue
    q = requests.get(f"{COMFY}/queue", timeout=30).json()
    for item in q.get("queue_running", []):
        if item[1] == prompt_id:
            return {"status": "running"}
    pending = [item[1] for item in q.get("queue_pending", [])]
    if prompt_id in pending:
        return {"status": "queued", "position": pending.index(prompt_id) + 1}
    return {"status": "running"}  # vừa nộp, chưa kịp xuất hiện


@app.get("/result/{prompt_id}")
def result(prompt_id: str):
    h = requests.get(f"{COMFY}/history/{prompt_id}", timeout=30).json()
    entry = h.get(prompt_id)
    im = _find_output_image(entry) if entry else None
    if not im:
        raise HTTPException(404, "Chưa có ảnh.")
    r = requests.get(
        f"{COMFY}/view",
        params={"filename": im["filename"], "subfolder": im.get("subfolder", ""), "type": "output"},
        timeout=60,
    )
    r.raise_for_status()
    return Response(content=r.content, media_type=r.headers.get("Content-Type", "image/png"))


if __name__ == "__main__":
    import uvicorn

    if _argos is None:
        print("CẢNH BÁO: chưa có argostranslate -> prompt gửi nguyên tiếng Việt (Flux hiểu kém).")
        print("Cài: pip install argostranslate  rồi tải gói vi->en (xem README-webapp.md).")
    print(f"Mở trên máy khác trong LAN: http://<IP-máy-này>:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)

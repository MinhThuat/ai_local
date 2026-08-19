# Hướng dẫn cài model: FLUX Kontext Q6 & Qwen-Image-Edit-2509

Máy đích: **RTX 3080 10GB VRAM + 32GB RAM**. Cả hai đều chạy trong **ComfyUI hiện có**, không cần phần mềm khác.

> Quy ước thư mục ComfyUI:
> - GGUF diffusion (unet) → `ComfyUI/models/unet/`
> - Text encoder → `ComfyUI/models/text_encoders/`
> - VAE → `ComfyUI/models/vae/`

---

## Phần A — FLUX Kontext Q6 (nâng cấp nhanh, chỉ 1 file)

Dùng để thay bản Q4 đang chạy. Nghe lệnh khá hơn, vẫn hợp 10GB (~9.8GB, offload nhẹ).
**Không đổi workflow, không đổi CLIP/VAE** — chỉ đổi 1 file unet.

**Tải:** repo `city96/FLUX.1-Kontext-dev-gguf`
- File: **`flux1-kontext-dev-Q6_K.gguf`** (~9.8GB)
- Link: https://huggingface.co/city96/FLUX.1-Kontext-dev-gguf/blob/main/flux1-kontext-dev-Q6_K.gguf

**Đặt vào:** `ComfyUI/models/unet/`

**Kích hoạt:** trong workflow Kontext hiện tại → node **Unet Loader (GGUF)** → đổi `unet_name` sang `flux1-kontext-dev-Q6_K.gguf`.
(Trong `webapp/workflow_api.json` là node `"1"`, field `unet_name`.)

> Muốn nhẹ hơn nếu chậm: `flux1-kontext-dev-Q5_K_M.gguf` (~8.4GB) cùng repo.

---

## Phần B — Qwen-Image-Edit-2509 (multi-ref, nghe lệnh + chữ tốt hơn)

Đây là **model + workflow MỚI**, khác kiến trúc FLUX → cần tải **3 file** và dựng graph mới.
Nhận **nhiều ảnh tham chiếu (tới 3)** — hợp ca ornament + màu chỉ + màu vải.

### Yêu cầu trước
- **Cập nhật ComfyUI** lên bản mới (để có node `TextEncodeQwenImageEdit`).
- **ComfyUI-GGUF** custom node (bạn đang chạy FLUX GGUF nên thường đã có). Nếu chưa: ComfyUI Manager → cài "ComfyUI-GGUF".

### 1. Diffusion model (GGUF)
Repo: `QuantStack/Qwen-Image-Edit-2509-GGUF`
- File: **`Qwen-Image-Edit-2509-Q4_K_S.gguf`** (~12GB) — bản khuyên dùng cho 10GB
- Link: https://huggingface.co/QuantStack/Qwen-Image-Edit-2509-GGUF
- Đặt vào: `ComfyUI/models/unet/`

> Muốn chất hơn (32GB RAM gánh được): `Qwen-Image-Edit-2509-Q4_K_M.gguf` (~13GB).
> Muốn nhẹ hơn nếu quá chậm: `...-Q3_K_M.gguf` (~9GB) — chất tụt, cân nhắc.

### 2. Text encoder — Qwen2.5-VL 7B
Chọn **một** trong hai:

**Cách 1 (khuyên dùng, đơn giản) — safetensors fp8:**
Repo: `Comfy-Org/Qwen-Image_ComfyUI`
- File: **`split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors`** (~8.5GB)
- Link: https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/tree/main/split_files/text_encoders
- Đặt vào: `ComfyUI/models/text_encoders/`
- Node dùng: **CLIPLoader** (type = `qwen_image`)

**Cách 2 (nhẹ hơn) — GGUF:**
Repo: `city96/Qwen2.5-VL-7B-Instruct-gguf`
- File: `Qwen2.5-VL-7B-Instruct-Q4_K_M.gguf` (~4.7GB)
- Link: https://huggingface.co/city96/Qwen2.5-VL-7B-Instruct-gguf
- Đặt vào: `ComfyUI/models/text_encoders/`
- Node dùng: **CLIPLoader (GGUF)** (type = `qwen_image`)

### 3. VAE
Repo: `Comfy-Org/Qwen-Image_ComfyUI`
- File: **`split_files/vae/qwen_image_vae.safetensors`** (~0.25GB)
- Link: https://huggingface.co/Comfy-Org/Qwen-Image_ComfyUI/tree/main/split_files/vae
- Đặt vào: `ComfyUI/models/vae/`

### 4. Dựng workflow
1. ComfyUI → menu **Workflow → Browse Templates** → tìm mẫu **"Qwen Image Edit"** (bản mới có sẵn). Mở lên.
2. Đổi các loader sang file vừa tải:
   - Diffusion: dùng **Unet Loader (GGUF)** → `Qwen-Image-Edit-2509-Q4_K_S.gguf`
   - Text encoder: **CLIPLoader / CLIPLoader (GGUF)**, type `qwen_image` → file Qwen2.5-VL
   - VAE: **Load VAE** → `qwen_image_vae.safetensors`
3. Multi-ref: dùng node **TextEncodeQwenImageEdit** — nối nhiều `LoadImage` vào (ornament / màu chỉ / màu vải), mô tả vai trò từng ảnh trong prompt.
4. Chạy thử 1 ảnh cho ra ok → **Save (API Format)** → lưu thành `webapp/workflow_qwen.json`.
5. Báo mình → mình chỉnh `server.py` nhận đúng node prompt Qwen + gửi nhiều ảnh vào 1 job.

---

## Ghi chú VRAM / tốc độ (10GB + 32GB RAM)

| Model | Tốc độ | Ghi chú |
|-------|--------|---------|
| FLUX Kontext **Q6** | Nhanh | Việc thường ngày, số lượng lớn |
| Qwen-Edit-2509 **Q4** | **~1.5–4 phút/ảnh** (offload RAM) | Ảnh hero, multi-ref; không hợp chạy loạt |

- Qwen tổng weights ~17GB > 10GB VRAM → ComfyUI tự đẩy phần dư sang RAM (32GB đủ, không thrash).
- Nếu ComfyUI báo hết VRAM (OOM): thêm cờ khởi động `--lowvram`, hoặc hạ quant Qwen xuống Q3.

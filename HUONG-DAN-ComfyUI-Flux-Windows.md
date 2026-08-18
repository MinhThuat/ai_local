# Quy trình gen ảnh Etsy bằng ComfyUI (Windows · RTX 3080 10GB · KHÔNG train)

> Sản phẩm: khung thêu tuỳ chỉnh (tên + motif Halloween/baby). Quy trình:
> **Tầng 1** — nhiều ảnh mẫu → nhiều design mới (giữ phong cách thêu).
> **Tầng 2** — 1 design → nhiều mockup đổi màu vải/chỉ, đổi bối cảnh.
> Không lập trình, không train. Tải model → nạp workflow → gõ lệnh.

---

## ⭐ NGUYÊN TẮC VÀNG (nhớ cái này là hiểu hết)

| Việc | Model | Vì sao |
|---|---|---|
| **TẠO** ảnh mới từ chữ | **Flux dev** | Model sinh ảnh |
| **SỬA** ảnh theo lệnh (đổi X giữ Y) | **Flux Kontext** | Model edit — *hiểu* lệnh |

> ❌ Flux dev **không sửa được** ảnh theo lệnh (đưa áo Hulk bảo đổi Ironman → nó
> không đổi, hoặc đổi thì phá luôn áo). Đó là lý do phải có **Kontext**.
> **dev = tạo mới · Kontext = sửa.**

---

## 1. CÁC MODEL CẦN TẢI

Mọi model Flux **dùng chung** 3 file encoder/VAE — tải 1 lần, xài cho tất cả.

### Dùng chung (nền tảng)

| File | Thư mục | Login? | Link |
|---|---|---|---|
| `t5xxl_fp8_e4m3fn.safetensors` (~4.9GB) | `models\clip\` | không | huggingface.co/comfyanonymous/flux_text_encoders |
| `clip_l.safetensors` (~250MB) | `models\clip\` | không | huggingface.co/comfyanonymous/flux_text_encoders |
| `ae.safetensors` (VAE ~335MB) | `models\vae\` | **có** | huggingface.co/black-forest-labs/FLUX.1-dev |

### Model chính

| File | Thư mục | Dùng cho | Link |
|---|---|---|---|
| **`flux1-kontext-dev-Q4_K_S.gguf`** (~6.8GB) | `models\unet\` | ⭐ SỬA — cả tầng 1 & 2 | huggingface.co/city96/FLUX.1-Kontext-dev-gguf |
| `flux1-dev-Q5_K_S.gguf` (~8.3GB) | `models\unet\` | TẠO mới từ số 0 | huggingface.co/city96/FLUX.1-dev-gguf |
| `4x-UltraSharp.pth` (~64MB) | `models\upscale_models\` | Phóng lên 2048px | huggingface.co/Kim2091/UltraSharp |

**Tổng cần tải:**
- Chạy được cả quy trình: **3 file chung + Kontext = 4 file.**
- Đủ ra ảnh Etsy 2048px: **+ upscaler = 5 file.**
- `flux1-dev` chỉ cần khi muốn gen từ số 0 (không có ảnh vào).

### Link tải trực tiếp (dán vào trình duyệt)
```
https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/t5xxl_fp8_e4m3fn.safetensors
https://huggingface.co/comfyanonymous/flux_text_encoders/resolve/main/clip_l.safetensors
https://huggingface.co/city96/FLUX.1-Kontext-dev-gguf/resolve/main/flux1-kontext-dev-Q4_K_S.gguf
https://huggingface.co/city96/FLUX.1-dev-gguf/resolve/main/flux1-dev-Q5_K_S.gguf
```
`ae.safetensors`: vào `black-forest-labs/FLUX.1-dev`, đăng nhập HuggingFace, bấm
**Agree** → tải `ae.safetensors` bỏ vào `models\vae\`. Kiểm tra file ~335MB (nếu
vài KB / là HTML → chưa login, làm lại).

`4x-UltraSharp.pth`: `huggingface.co/Kim2091/UltraSharp/tree/main` → tải file `.pth`.

---

## 2. CÀI ĐẶT (đã xong nếu ComfyUI chạy được)

- ComfyUI portable ở `C:\...\ComfyUI_windows_portable`, chạy `run_nvidia_gpu.bat`.
- **Driver NVIDIA** phải mới (đã update, `nvidia-smi` báo CUDA ≥ 12.8).
- Node **ComfyUI-GGUF** đã cài qua Manager (để nạp file `.gguf`).
- Node upscale (ImageUpscaleWithModel) là node gốc — không cần cài thêm.

---

## 3. WORKFLOW THEO TỪNG VIỆC

### 🔹 TẦNG 1 — nhiều ảnh mẫu → design mới (Kontext)

1. **Workflow ▸ Browse Templates ▸ Flux ▸ Flux Kontext dev** → nạp template.
2. Node loader `.safetensors` → chuột phải ▸ Remove → thay **Unet Loader (GGUF)**
   → chọn `flux1-kontext-dev-Q4_K_S.gguf` → nối lại dây MODEL.
3. Node **Load Image** → nạp ảnh mẫu thật (satin stitch / khung oval).
4. Prompt (lệnh) — ví dụ:
   ```
   In the same real satin-stitch machine-embroidery style as the reference
   (faux-wood hoop, brass ring, small satin bow, flat embroidered-patch look),
   create a new design: fabric = sage green gingham, a cute embroidered baby
   BUNNY motif, name "Isla" in bold rounded embroidered script above "GRACE"
   in spaced uppercase serif, single forest-green thread color, name high in
   the upper-middle, motif centered below. Photorealistic product photo.
   ```
5. guidance ~2.5–3, steps ~20–24 → **Run**.

### 🔹 TẦNG 2 — 1 design → đổi màu vải/chỉ (Kontext)

Cùng template Kontext, chỉ đổi ảnh vào + lệnh:
1. **Load Image** → nạp 1 design đã có.
2. Prompt:
   ```
   Keep the embroidered hoop design, name, spelling, motif, layout and hoop
   shape EXACTLY the same. Only change the fabric to burnt-orange linen and
   the thread color to cream. Same real satin-stitch embroidery, same lighting.
   ```
3. Đổi màu khác = đổi 2 chữ màu → chạy lại. Loop qua bảng màu = ra cả bộ.

### 🔹 TẦNG 2b — đổi bối cảnh mockup (Kontext)

```
Keep the exact embroidered sign (same name, fabric, bow, motif, hoop) unchanged.
Place it {standing on a wooden nursery shelf next to a teddy bear and a lit
candle}. Photorealistic cozy nursery, soft daylight, the sign in clear focus.
```
Đổi phần `{...}`: mẹ bế bé / flatlay hoa khô / treo tường / tay cầm như quà…

### 🔹 TẠO MỚI TỪ SỐ 0 (khi không có ảnh vào) — Flux dev

Nạp file `flux-gguf-txt2img.json` → gõ prompt tả sản phẩm → Run.
(Chỉ dùng khi không có ảnh tham chiếu. Có ảnh thì luôn dùng Kontext.)

### 🔹 UPSCALE lên 2048px cho Etsy

Nạp file `flux-gguf-txt2img-upscale.json` (đã có node upscale ghép sẵn), hoặc
thêm 2 node vào workflow bất kỳ:
```
Load Upscale Model (4x-UltraSharp.pth) → Upscale Image (using Model) → Save Image
VAE Decode .IMAGE → Upscale Image (using Model) .image
```

---

## 4. FILE WORKFLOW CÓ SẴN (kéo–thả vào ComfyUI)

| File | Dùng |
|---|---|
| `flux-gguf-txt2img.json` | Tạo mới từ chữ (Flux dev) |
| `flux-gguf-txt2img-upscale.json` | Tạo mới + phóng 2048px |
| `flux-gguf-img2img.json` | Biến đổi 1 ảnh theo % (ít dùng — thích Kontext hơn) |
| Tầng 1 & 2 (Kontext) | Dùng **template có sẵn** của ComfyUI (node Kontext đổi theo phiên bản, template chắc ăn hơn) |

---

## 5. VẬN HÀNH TRÊN 10GB

- **1 GPU = 1 ảnh 1 lúc.** Không chạy song song được. Bấm Run nhiều lần → xếp hàng.
- **Đừng nạp dev + Kontext cùng lúc** → tràn VRAM. Làm theo mẻ:
  1. Kontext: gen hết design (tầng 1) + đổi màu/cảnh (tầng 2).
  2. Cần gen từ số 0 thì mới đổi sang dev.
  - Mỗi lần đổi model nạp lại ~30–60s.
- Ảnh đầu tiên ~1–3 phút (nạp model), sau đó ~50–90s/ảnh (Kontext).
- Hết VRAM → sửa `.bat` thêm `--lowvram`, hoặc dùng model Q4.

---

## 6. ĐIỂM YẾU & CÁCH GIẢM

- **Tên có thể sai chính tả** (điểm yếu của model local so với gpt-image-1).
  - Tầng 2 (đổi màu/cảnh): tên đứng yên → ít sai.
  - Tầng 1 (gen mới): sai nhiều hơn → chạy lại vài seed chọn cái đúng, hoặc
    tải thêm **Flux Fill (inpaint)** vẽ lại đúng vùng tên.
- Tên: dùng chữ **Latin, bỏ dấu** (Bảo → `Bao`). Prompt viết **tiếng Anh**.

---

## 7. KHÔNG TRAIN

Toàn bộ trên **không train gì**. Kontext nhận ảnh + lệnh, giống hệt cách pipeline
OpenAI cũ đưa `-i sample.jpg`. Chỉ cân nhắc train 1 **style LoRA** SAU NÀY nếu chạy
Kontext thấy phong cách trôi giữa các design — và train thì thuê cloud 30 phút,
không train trên 10GB.

---

## TÓM TẮT 1 DÒNG
Tải **Kontext + 3 file chung + upscaler (5 file)** → dùng **template Kontext**:
đưa ảnh + gõ lệnh "giữ X đổi Y" cho cả tạo design lẫn đổi màu/cảnh. **dev để tạo
mới, Kontext để sửa.** Không train.

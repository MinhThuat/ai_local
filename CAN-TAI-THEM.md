# Cần tải THÊM (so với bản cài ban đầu)

> Bản đầu đã có: `flux1-dev-Q5`, `t5xxl_fp8`, `clip_l`, `ae.safetensors`.
> Dưới đây CHỈ những cái MỚI cần thêm cho quy trình Kontext.

## 1. Model Kontext — BẮT BUỘC

| Tải gì | Link | Đặt vào |
|---|---|---|
| `flux1-kontext-dev-Q4_K_S.gguf` (~6.8GB) | https://huggingface.co/QuantStack/FLUX.1-Kontext-dev-GGUF/resolve/main/flux1-kontext-dev-Q4_K_S.gguf | `ComfyUI\models\unet\` |


## 2. Model upscale — NÊN CÓ (ảnh Etsy 2048px, chỉ 64MB)

| Tải gì | Link | Đặt vào |
|---|---|---|
| `4x-UltraSharp.pth` (~64MB) | https://huggingface.co/Kim2091/UltraSharp/resolve/main/4x-UltraSharp.pth | `` |

→ Thư mục `upscale_models` chưa có thì tự tạo.

## 3. File workflow — kéo–thả vào ComfyUI

Chép từ ổ chung sang máy Windows, rồi kéo vào cửa sổ ComfyUI:

| File | Dùng |
|---|---|
| `flux-kontext-all-in-one.json` | ⭐ Làm HẾT: tạo design, đổi màu vải/chỉ, đổi cảnh. Nạp ảnh + gõ lệnh. |

Đường dẫn file: `/mnt/6C96C1A096C16AE2/vsc/AI-LOCAL/flux-kontext-all-in-one.json`

---

## Tóm tắt
- Tải **1 file bắt buộc** (Kontext) + **1 file nên có** (upscaler).
- Không tải lại encoder/VAE.
- Không cần model con nào khác (Redux/ControlNet/Fill/LoRA) lúc này.
- Không train.

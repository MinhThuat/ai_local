# Web app đơn giản gen ảnh Kontext qua LAN

**Ngày:** 2026-08-17
**Mục tiêu:** Che hết ComfyUI. Cho nhiều người trong LAN cùng dùng 1 GPU: nạp ảnh + gõ lệnh (tiếng Việt) → nhận ảnh 2048×2048, kết quả hiện lần lượt như chat. Bấm là xếp hàng.

## Ràng buộc & quyết định

- **Chỉ 1 chế độ:** sửa ảnh bằng **Flux Kontext**. Luôn cần ảnh vào. KHÔNG có "tạo mới từ chữ" (Flux dev) → chỉ 1 model, không đổi model, VRAM ổn định trên RTX 3080 10GB.
- **Nhiều ảnh = hàng loạt:** N ảnh + 1 lệnh chung → N job **riêng biệt** → N ảnh kết quả. Không ghép ảnh.
- **Prompt tiếng Việt**, dịch sang tiếng Anh bằng **Argos Translate** (CPU, offline, miễn phí, không đụng GPU) trước khi gửi Flux.
- **Output ép 2048×2048** (upscale). Ảnh không vuông sẽ méo — chấp nhận (sản phẩm khung thêu gần vuông). Là nút chỉnh.
- **1 GPU = xếp hàng.** Không tự viết queue — dùng queue sẵn có của ComfyUI.
- **Không login, không tài khoản.** Mỗi trình duyệt tự nhớ job của mình (localStorage). Shop nhỏ, LAN tin cậy.

## Kiến trúc

```
Trình duyệt (LAN)  →  FastAPI :8000 (máy Windows, bind 0.0.0.0)  →  ComfyUI :8188 (localhost)
```

- Người dùng chỉ chạm FastAPI. ComfyUI ở localhost, không mở ra LAN (an toàn hơn).
- Mở firewall Windows cổng **8000**.

## Thành phần

### 1. Server — `server.py` (FastAPI + uvicorn, 1 file)

Endpoint:

- `POST /generate` — multipart: `prompt` (str, tiếng Việt) + `images` (1..N file).
  1. Dịch `prompt` VI→EN **một lần** (Argos), dùng chung cho mọi ảnh.
  2. Với **mỗi ảnh**:
     - Upload ảnh sang ComfyUI: `POST /upload/image`.
     - Nạp template workflow Kontext (định dạng **API**), thay `{image_name}` + `{prompt_en}`, ép output 2048×2048.
     - Gửi: `POST /prompt` → nhận `prompt_id`.
  3. Trả JSON: `[{prompt_id, input_filename}, ...]`.

- `GET /status/{prompt_id}` — hỏi ComfyUI `GET /history/{prompt_id}`:
  - Chưa có trong history → đang xếp hàng / đang chạy (phân biệt qua `GET /queue` nếu cần vị trí hàng).
  - Có → trạng thái `done` + tên file output.

- `GET /result/{prompt_id}` — proxy ảnh output từ ComfyUI `GET /view?filename=...` (đúng subfolder/type).

Cấu hình đầu file: `COMFY = "http://127.0.0.1:8188"`, `STEPS`, `GUIDANCE`, `OUTPUT_SIZE = 2048`.

### 2. Workflow template — `kontext_api.json`

- Định dạng **API** (không phải file `.json` UI hiện có). Dựng từ workflow Kontext của người dùng.
- Chuỗi node: `UnetLoaderGGUF(flux1-kontext-dev-Q4_K_S)` → `DualCLIPLoader(t5xxl_fp8, clip_l)` → `CLIPTextEncode({prompt_en})` → `LoadImage({image_name})` → (Kontext reference/latent) → `KSampler(steps, guidance)` → `VAEDecode(ae)` → upscale/resize **2048×2048** → `SaveImage`.
- Placeholder: `{image_name}`, `{prompt_en}`.
- **PHẢI test trên ComfyUI thật** (máy Windows) — không chạy được từ máy dev này.

### 3. Trang — `index.html` (1 file, phục vụ bởi FastAPI)

- Ô textarea prompt + input chọn **nhiều ảnh** + nút "Gửi".
- Sau khi gửi: mỗi ảnh tạo 1 **thẻ** trong feed dọc (như chat): ảnh gốc thu nhỏ + trạng thái ("Đang xếp hàng #k" / "Đang chạy…" / "✅") + ảnh kết quả 2048 khi xong.
- Poll `GET /status/{id}` mỗi ~2s cho job chưa xong. Xong cái nào hiện cái đó (lần lượt theo GPU trả).
- `localStorage` lưu danh sách job (id + input thumbnail) để giữ qua F5.

## Luồng dữ liệu

1. Người dùng chọn 5 ảnh + gõ "đổi vải sang cam" → Gửi.
2. Server dịch → "change fabric to orange", tạo 5 job Kontext, trả 5 `prompt_id`.
3. ComfyUI xếp 5 job lên GPU, chạy tuần tự (~50–90s/ảnh).
4. Trang poll, thẻ nào xong hiện ảnh 2048 đó — lần lượt.

## Lỗi & xử lý

- Không có ảnh → 400, báo "cần ít nhất 1 ảnh".
- Argos thiếu gói vi→en → server báo lỗi rõ khi khởi động (cài gói 1 lần).
- ComfyUI không chạy / lỗi `/prompt` → thẻ hiện "❌ ComfyUI lỗi", không làm sập cả trang.
- Job lỗi trong ComfyUI (history có `status: error`) → thẻ hiện "❌", cho gửi lại.

## Kiểm thử (ponytail: 1 check chạy được)

- `test_translate.py` — assert Argos dịch 1 câu VI ra chuỗi tiếng Anh không rỗng, khác input.
- Verify workflow Kontext end-to-end **thủ công trên ComfyUI thật** (không mock được GPU).

## Ngoài phạm vi (YAGNI)

- Không login/tài khoản, không gallery chung server-side.
- Không tạo mới từ chữ (Flux dev), không ghép nhiều ảnh thành 1.
- Không chọn tỉ lệ ảnh (cứng 2048 vuông), không chỉnh steps/guidance từ UI.
- Không dịch online (Google/Claude API) — Argos offline là đủ.

## Vận hành

- Máy Windows: chạy ComfyUI (như hiện tại) + `python server.py`.
- Cài 1 lần: `pip install fastapi uvicorn python-multipart argostranslate requests` + tải gói Argos vi→en.
- Người dùng: `http://<IP-máy-Windows>:8000`.

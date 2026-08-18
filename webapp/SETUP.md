# Runbook: set up cho flow trơn tru

Hai máy: **MÁY BẠN** (sửa code) và **MÁY AI** (Windows, chạy ComfyUI + share).

---

## A. MÁY BẠN (dev) — làm 1 LẦN

1. Cài Git (https://git-scm.com).
2. Đưa code lên GitHub (repo **public** cho gọn):
   ```
   cd <thư mục dự án>
   git init && git add . && git commit -m "webapp"
   git remote add origin https://github.com/<bạn>/<repo>.git
   git push -u origin main
   ```
   > `workflow_api.json` đã bị `.gitignore` — không lên GitHub (file riêng máy AI).

### Hằng ngày (mỗi lần sửa code)
```
git commit -am "sửa gì đó" && git push
```
→ trong ≤60s máy AI tự pull + restart. Xong.

---

## B. MÁY AI (Windows) — làm 1 LẦN

1. **ComfyUI** chạy được (`run_nvidia_gpu.bat`) — như hiện tại.
2. **Python deps**:
   ```
   pip install fastapi "uvicorn[standard]" python-multipart requests argostranslate
   ```
3. **Gói dịch Argos vi→en** (offline, CPU):
   ```
   python -c "import argostranslate.package as p; p.update_package_index(); pkg=next(x for x in p.get_available_packages() if x.from_code=='vi' and x.to_code=='en'); p.install_from_path(pkg.download())"
   ```
4. **cloudflared**: tải https://github.com/cloudflare/cloudflared/releases (file `.exe`), để vào PATH
   (hoặc cùng thư mục webapp).
5. **Clone repo**:
   ```
   git clone https://github.com/<bạn>/<repo>.git
   cd <repo>/webapp
   ```
6. **Export workflow** từ ComfyUI:
   - ComfyUI → Settings → bật **Dev mode**.
   - Nạp workflow Kontext chạy ngon (**có node upscale ra 2048×2048**).
   - Đặt **Title node prompt** (CLIPTextEncode dương) = `PROMPT` (chuột phải node → Title).
   - Menu → **Save (API Format)** → lưu thành `webapp/workflow_api.json`.
   > **Không cần node/model dịch trong graph.** Dịch VI→EN do Argos lo (bước B.3, chạy CPU
   > ngoài ComfyUI). Nếu graph có node dịch thì **xoá đi** — prompt tiếng Anh từ webapp đi
   > thẳng vào node `PROMPT`. Graph chỉ cần: Kontext + t5xxl + clip_l + ae(VAE) + upscale.

### Kiểm tra nhanh 1 lần
```
python test_translate.py      # thấy "OK: ..." (bản dịch tiếng Anh)
```

### KHÔNG muốn cài Git trên máy AI? (chỉ cần Python)
Bỏ qua bước clone (B.5). Thay vào đó:
1. Tải mỗi 1 file `autosync_nogit.py` từ GitHub (mở file trên web → Raw → lưu về) vào 1 folder rỗng,
   ví dụ `C:\webapp`.
2. Export `workflow_api.json` vào cùng folder đó (bước B.6).
3. Sửa `start-ai-nogit.bat` (điền `GH_OWNER`, `GH_REPO`) — hoặc chạy tay:
   ```
   set GH_OWNER=tenban & set GH_REPO=tenrepo
   python autosync_nogit.py
   ```
   Nó tự tải toàn bộ code còn lại từ GitHub (zip qua HTTPS), start server, và cứ 60s kiểm tra
   code mới → tải lại + restart. Không cần `git` gì cả.
   > Mục C dùng `start-ai-nogit.bat` thay cho `start-ai.bat`.
   > Repo private thì thêm `set GH_TOKEN=<token>`.

---

## C. MÁY AI — MỖI LẦN KHỞI ĐỘNG

1. Chạy ComfyUI (`run_nvidia_gpu.bat`) nếu chưa chạy.
2. Trong `webapp/` chạy:
   ```
   start-ai.bat
   ```
   Nó mở 2 thứ: `autosync.py` (tự sync + restart server) và `cloudflared` (→ cổng 8000).
3. Cửa sổ cloudflared hiện link `https://xxx.trycloudflare.com` → **gửi link đó cho người dùng**.
   - Giữ 2 cửa sổ này mở là hệ thống sống.
   - Link chỉ đổi khi bạn tắt/mở lại cloudflared (không đổi khi sync code).

---

## D. Kiểm tra flow chạy đúng

- Mở link → chọn ảnh + gõ lệnh tiếng Việt → bấm Gửi → ảnh 2048 hiện ra, có nút **⬇ Tải về**.
- Ở máy bạn: sửa 1 dòng, `git push` → nhìn cửa sổ autosync trên máy AI, trong ≤60s phải thấy
  `autosync: có code mới ... -> pull + restart`. Link Cloudflare **không đổi**.

## Nếu lỗi
- Thẻ ảnh báo "❌ ComfyUI báo lỗi" → workflow_api.json sai (thiếu node / title prompt chưa đặt).
- `autosync: pull lỗi` → máy AI có sửa file local đụng với GitHub. Vào `webapp/` chạy `git status`,
  bỏ thay đổi thừa (`git checkout -- .`) rồi để nó pull lại.
- Prompt gửi nguyên tiếng Việt → chưa cài gói Argos vi→en (làm lại B.3), hoặc tạm gõ tiếng Anh.

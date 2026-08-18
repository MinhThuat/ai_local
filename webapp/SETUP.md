# Runbook đầy đủ: webapp gen ảnh Kontext qua LAN/Cloudflare

Hai máy:
- **MÁY BẠN (dev)** — sửa code, push lên GitHub.
- **MÁY AI (Windows)** — chạy ComfyUI, nhận code tự động, share link cho người dùng.

Luồng: bạn `git push` → máy AI tự nhận trong ≤60s + restart → người dùng F5.
Người dùng chỉ thấy 1 trang đơn giản: chọn ảnh + gõ lệnh **tiếng Việt** → nhận ảnh 2048×2048.

---

## A. MÁY BẠN (dev) — làm 1 LẦN

1. Cài Git: https://git-scm.com — và có tài khoản GitHub.

2. Nếu Git báo `dubious ownership` (hay gặp trên ổ mount/NTFS):
   ```
   git config --global --add safe.directory <đường-dẫn-thư-mục>
   ```

3. Đặt tên/email cho Git (nếu chưa):
   ```
   git config --global user.name "Ten"
   git config --global user.email "mail@abc.com"
   ```

4. Tạo 1 repo **rỗng** trên github.com (New → đặt tên → **Public** → KHÔNG tích "Add README").
   > Public cho gọn: code này không có bí mật. `workflow_api.json` đã bị `.gitignore`.

5. Trong thư mục dự án, đẩy code lên:
   ```
   git init
   git add .
   git commit -m "webapp"
   git branch -M main
   git remote add origin https://github.com/<bạn>/<repo>.git
   git push -u origin main
   ```

6. Khi push hỏi mật khẩu → GitHub KHÔNG nhận mật khẩu tài khoản, phải dùng **Personal Access Token**:
   - github.com → Settings → Developer settings → Personal access tokens → **Tokens (classic)**
     → Generate → tích quyền **`repo`** → copy token.
   - Lúc `git push`: **Username** = tên GitHub, **Password** = dán token.

### Hằng ngày (mỗi lần sửa code)
```
git commit -am "sửa gì đó"
git push
```
→ máy AI tự nhận trong ≤60s. Xong.

---

## B. MÁY AI (Windows) — CÀI 1 LẦN

1. **ComfyUI** chạy được (`run_nvidia_gpu.bat`).

2. **Python deps**:
   ```
   pip install fastapi "uvicorn[standard]" python-multipart requests argostranslate
   ```

3. **Gói dịch Argos vi→en** (offline, chạy CPU — KHÔNG đụng GPU):
   ```
   python -c "import argostranslate.package as p; p.update_package_index(); pkg=next(x for x in p.get_available_packages() if x.from_code=='vi' and x.to_code=='en'); p.install_from_path(pkg.download())"
   ```
   > Nhờ cái này người dùng gõ **tiếng Việt** được. Chưa cài thì app vẫn chạy nhưng gửi
   > nguyên tiếng Việt cho Flux (ảnh sai) → khi đó phải gõ tiếng Anh.

4. **cloudflared**: tải `cloudflared.exe` từ
   https://github.com/cloudflare/cloudflared/releases → để vào PATH hoặc cùng folder webapp.

5. **Lấy code** — chọn 1 trong 2:

   **Cách 1 — KHÔNG cần cài Git (chỉ Python) [khuyên dùng nếu ngại cài Git]:**
   - Tạo folder rỗng, ví dụ `C:\webapp`.
   - Vào repo GitHub → mở file `webapp/autosync_nogit.py` → nút **Raw** → lưu vào `C:\webapp\`.
   - Chỉ cần **1 file này**, nó tự tải toàn bộ code còn lại khi chạy (mục C).

   **Cách 2 — có cài Git:**
   ```
   git clone https://github.com/<bạn>/<repo>.git
   ```
   Code nằm trong `<repo>/webapp`. (Clone ra folder RIÊNG, ĐỪNG bỏ vào folder ComfyUI.)

6. **Export workflow từ ComfyUI** → lưu thành `workflow_api.json` (cùng folder webapp):
   - ComfyUI → Settings → bật **Dev mode**.
   - Nạp workflow Kontext chạy ngon (**có node upscale ra 2048×2048**).
   - Node prompt (CLIPTextEncode **dương**) → chuột phải → **Title = `PROMPT`**.
   - Menu → **Save (API Format)** → lưu thành `workflow_api.json`.
   > **KHÔNG cần node/model dịch trong graph** — dịch do Argos lo (bước 3). Nếu graph có node
   > dịch thì **xoá đi**. Graph chỉ cần: Kontext + t5xxl + clip_l + ae(VAE) + upscale
   > (các model text-encoder/VAE đã có sẵn từ bản cài đầu).

### Kiểm tra nhanh (nếu dùng cách clone/có code sẵn)
```
python test_translate.py      # ra "OK: ..." (bản dịch tiếng Anh) = Argos OK
```

---

## C. MÁY AI — MỖI LẦN KHỞI ĐỘNG

1. Chạy ComfyUI (`run_nvidia_gpu.bat`) nếu chưa chạy.

2. Trong folder webapp, chạy **1 trong 2** (khớp với cách ở B.5):

   **Cách 1 (no-git):** sửa `start-ai-nogit.bat`, điền `GH_OWNER` và `GH_REPO`, rồi chạy nó.
   Hoặc chạy tay:
   ```
   set GH_OWNER=<bạn> & set GH_REPO=<repo>
   python autosync_nogit.py
   ```

   **Cách 2 (git):** chạy `start-ai.bat` (hoặc `python autosync.py`).

3. Mở tunnel (nếu bat chưa tự mở):
   ```
   cloudflared tunnel --url http://localhost:8000
   ```
   Cửa sổ này hiện link `https://xxx.trycloudflare.com` → **gửi link cho người dùng**.

Giữ 2 cửa sổ (autosync + cloudflared) mở là hệ thống sống.

> **Cổng 8000** là của webapp, KHÔNG phải 8188 của ComfyUI. ComfyUI ở local, webapp là cái public.
> **cloudflared chạy RIÊNG** với autosync → khi sync code, server restart ~2s nhưng **link KHÔNG đổi**.
> Link chỉ đổi khi bạn tắt/mở lại cloudflared (muốn URL cố định → named tunnel, cần domain).

---

## D. NGHIỆM THU

1. Mở link `trycloudflare.com` → chọn 1 hoặc nhiều ảnh + gõ lệnh tiếng Việt → **Gửi**.
   → mỗi ảnh ra 1 kết quả 2048×2048, hiện lần lượt, có nút **⬇ Tải về** (ảnh lưu về máy bạn).
2. Ở máy bạn: `git commit -am "test" && git push` → nhìn cửa sổ autosync trên máy AI,
   trong ≤60s thấy `có code mới → cập nhật/pull → restart`. Link Cloudflare **không đổi**.

---

## E. NHỚ / GIỚI HẠN

- **1 GPU = xếp hàng.** N ảnh → N job chạy tuần tự (~50–90s/ảnh). Đông người = đợi lâu hơn.
- Chỉ chế độ **sửa ảnh (Kontext)** — luôn cần ảnh vào. Không có "tạo mới từ chữ".
- Output 2048×2048 nằm trong `workflow_api.json` của bạn, không phải trong code.
- Job ComfyUI đang chạy **không bị** restart làm hỏng (nằm trong queue riêng của ComfyUI).
- Nhịp sync 60s dùng `git fetch`/HTTP có ETag → **không bị GitHub coi là spam**.
  Chỉnh nhịp: `set SYNC_INTERVAL=30`.

### git vs no-git (chọn ở B.5)
| | `autosync.py` (git) | `autosync_nogit.py` (zip) |
|---|---|---|
| Cần cài | Git + clone 1 lần | Chỉ Python |
| Lấy code mới | pull delta (nhẹ hơn khi repo lớn) | tải zip (repo bé thì như nhau) |
| Xoá file đã xoá khỏi repo | ✅ | ❌ (file cũ nằm lại) |
| Sửa nhầm code trên máy AI | pull dừng, báo lỗi (an toàn) | ghi đè im lặng |
Repo bé thì hiệu năng như nhau → chọn theo "có cài Git được không".
No-git: đừng sửa code tay trên máy AI; thi thoảng xoá folder cho tải lại sạch.

## F. LỖI THƯỜNG GẶP

- Thẻ ảnh "❌ ComfyUI báo lỗi" → `workflow_api.json` sai: thiếu node, hoặc chưa đặt Title `PROMPT`.
- `autosync: pull lỗi` (bản git) → máy AI có sửa file đụng GitHub. Trong folder chạy
  `git checkout -- .` rồi để nó pull lại.
- Prompt gửi nguyên tiếng Việt → chưa cài gói Argos vi→en (làm lại B.3), hoặc tạm gõ tiếng Anh.
- `dubious ownership` khi push (máy bạn) → `git config --global --add safe.directory <path>`.
- Link Cloudflare đổi sau khi sync → bạn đang để cloudflared bị restart chung với server;
  chạy cloudflared ở cửa sổ riêng (như `start-ai*.bat` làm).

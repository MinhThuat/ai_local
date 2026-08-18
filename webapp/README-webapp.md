# Web app gen ảnh Kontext qua LAN

Nạp N ảnh + 1 lệnh (tiếng Việt) → N job Kontext riêng → kết quả hiện lần lượt như chat.
Người dùng không đụng ComfyUI. GPU tự xếp hàng (queue của ComfyUI).

## 1. Cài (làm 1 lần, trên máy Windows chạy ComfyUI)

```
pip install fastapi "uvicorn[standard]" python-multipart requests argostranslate
```

Tải gói dịch vi→en của Argos (offline, chạy CPU):

```
python -c "import argostranslate.package as p; p.update_package_index(); \
pkg=next(x for x in p.get_available_packages() if x.from_code=='vi' and x.to_code=='en'); \
p.install_from_path(pkg.download())"
```

> Nếu không có gói vi→en trực tiếp: app vẫn chạy, chỉ là gửi prompt nguyên tiếng Việt
> (Flux hiểu kém hơn) — khi đó gõ prompt tiếng Anh.

## 2. Lấy workflow (QUAN TRỌNG — phần dễ vướng nhất)

App KHÔNG tự bịa workflow. Bạn export từ ComfyUI đang chạy được:

1. Mở ComfyUI → dựng/nạp workflow **Kontext** chạy ngon (có node upscale để ra **2048×2048**).
2. Settings → bật **Dev mode** (Enable dev mode options).
3. Menu → **Save (API Format)** → lưu thành `webapp/workflow_api.json`.
4. Trong workflow, click node prompt (CLIPTextEncode **dương**) → đặt **Title = `PROMPT`**
   (chuột phải node → Title). App vá đúng node này. Nếu chỉ có 1 node CLIPTextEncode thì khỏi cần.
5. Node **Load Image** giữ nguyên — app tự thay ảnh vào đó.

## 3. Chạy

```
python server.py
```

- Mặc định `0.0.0.0:8000`. ComfyUI phải đang chạy ở `127.0.0.1:8188`.
- Mở **firewall Windows** cho cổng **8000** (inbound).
- Máy khác trong LAN vào: `http://<IP-máy-Windows>:8000`
  (xem IP: `ipconfig` → IPv4 Address).

## 4. Kiểm tra dịch

```
python test_translate.py
```

## 5. Tự sync code từ GitHub + share qua Cloudflare (tuỳ chọn)

Mục tiêu: bạn sửa code ở máy mình → push → máy AI tự pull + restart, người dùng chỉ F5.

### 5.1. Máy bạn (dev) — đưa code lên GitHub 1 lần
```
cd <thư mục dự án>
git init && git add . && git commit -m "webapp"
# tạo repo trên github.com (để PUBLIC cho khỏi lo token khi pull), rồi:
git remote add origin https://github.com/<bạn>/<repo>.git
git push -u origin main
```
> `workflow_api.json` đã bị `.gitignore` — không lên GitHub (nó là file riêng của máy AI).
> Repo này chỉ là code webapp, không có bí mật → để **public** là gọn nhất.
> Lần sau sửa code: `git commit -am "..." && git push` là xong.

### 5.2. Máy AI (Windows, chạy ComfyUI) — clone + tự sync
```
git clone https://github.com/<bạn>/<repo>.git
cd <repo>/webapp
# export workflow_api.json từ ComfyUI (mục 2) vào đây
python autosync.py          # chạy cái này THAY cho python server.py
```
`autosync.py` sẽ tự chạy `server.py`, cứ 60s fetch GitHub, thấy commit mới thì pull + restart.
(Đổi nhịp: đặt biến `SYNC_INTERVAL`, ví dụ `set SYNC_INTERVAL=30`.)
Dùng `git fetch` (không phải REST API) nên nhịp 30–60s không bị GitHub coi là spam.

- Repo **private** → cần đăng nhập git 1 lần (Git Credential Manager) hoặc deploy key SSH.
- Job ComfyUI đang chạy **không bị** restart làm hỏng (nằm trong queue riêng của ComfyUI).
  Trình duyệt người dùng chỉ lỡ vài giây rồi tự poll lại.

### 5.3. Share ra ngoài bằng Cloudflare (link free)
Trỏ tunnel vào **webapp (8000)**, KHÔNG phải ComfyUI (8188):
```
cloudflared tunnel --url http://localhost:8000
```
→ ra link `https://xxx.trycloudflare.com`. Gửi link đó cho người dùng. ComfyUI vẫn ở localhost.
> Quick tunnel free đổi URL mỗi lần chạy lại. Muốn URL cố định thì dùng named tunnel (cần domain).

**Gộp sẵn:** chạy `start-ai.bat` — nó mở `autosync.py` (cửa sổ riêng) rồi mở cloudflared→8000.
Vì cloudflared chạy tách khỏi autosync nên **sync code không làm đổi link Cloudflare**
(autosync chỉ restart `server.py`, không đụng cloudflared). Link chỉ đổi khi bạn tắt/mở lại cloudflared.

## Ghi nhớ

- **1 GPU = xếp hàng.** N ảnh → N job chạy tuần tự (~50–90s/ảnh). Đông người = đợi lâu hơn, không tránh được.
- Chỉ chế độ **sửa ảnh (Kontext)** — luôn cần ảnh vào. Không có "tạo mới từ chữ".
- Output 2048×2048 nằm trong `workflow_api.json` của bạn, không phải trong code.
- Chỉnh cổng/URL bằng biến môi trường: `COMFY_URL`, `PORT`, `HOST`.

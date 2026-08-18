"""
Tự sync code từ GitHub KHÔNG cần cài Git — chỉ cần Python (đã có sẵn cho ComfyUI).
Tải zip repo qua HTTPS bằng thư viện chuẩn, giải nén, restart server.

Máy AI chỉ cần MỖI file này. Chạy nó -> nó tự tải hết code còn lại + start server.

Cài đặt trước khi chạy (đặt tên repo GitHub của bạn):
    set GH_OWNER=tenban
    set GH_REPO=tenrepo
    set GH_BRANCH=main          (mặc định main)
    set GH_TOKEN=xxx            (chỉ cần nếu repo PRIVATE)
    python autosync_nogit.py
"""
import hashlib
import io
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile

OWNER = os.environ.get("GH_OWNER", "")
REPO = os.environ.get("GH_REPO", "")
BRANCH = os.environ.get("GH_BRANCH", "main")
TOKEN = os.environ.get("GH_TOKEN", "")
INTERVAL = int(os.environ.get("SYNC_INTERVAL", "60"))
HERE = os.path.dirname(os.path.abspath(__file__))
URL = f"https://codeload.github.com/{OWNER}/{REPO}/zip/refs/heads/{BRANCH}"

# File riêng của máy AI — KHÔNG ghi đè khi sync
KEEP = {"workflow_api.json"}


def fetch(etag):
    """Trả (bytes_zip, etag_moi). Nếu không đổi -> (None, etag)."""
    req = urllib.request.Request(URL)
    if TOKEN:
        req.add_header("Authorization", f"token {TOKEN}")
    if etag:
        req.add_header("If-None-Match", etag)
    try:
        r = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return None, etag
        raise
    return r.read(), r.headers.get("ETag")


def extract_code(zip_bytes):
    """Ghi các file trong thư mục webapp của repo vào HERE (trừ KEEP)."""
    z = zipfile.ZipFile(io.BytesIO(zip_bytes))
    names = z.namelist()
    server = next((n for n in names if n.endswith("server.py")), None)
    if not server:
        raise RuntimeError("Không thấy server.py trong repo — sai GH_REPO/BRANCH?")
    prefix = server[: -len("server.py")]  # ví dụ 'reponame-main/webapp/'
    for n in names:
        if n.endswith("/") or not n.startswith(prefix):
            continue
        rel = n[len(prefix):]
        if rel in KEEP:
            continue
        dest = os.path.join(HERE, rel)
        os.makedirs(os.path.dirname(dest) or HERE, exist_ok=True)
        with z.open(n) as src, open(dest, "wb") as out:
            shutil.copyfileobj(src, out)


def start_server():
    return subprocess.Popen([sys.executable, "server.py"], cwd=HERE)


def restart(proc):
    if proc:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        time.sleep(2)
    return start_server()


def main():
    if not OWNER or not REPO:
        sys.exit("Chưa đặt GH_OWNER / GH_REPO. Xem hướng dẫn đầu file.")
    proc = None
    etag = None
    last_hash = None
    print(f"autosync (no-git): {OWNER}/{REPO}@{BRANCH}, poll mỗi {INTERVAL}s")
    try:
        while True:
            try:
                data, etag = fetch(etag)
            except Exception as e:
                print(f"autosync: tải lỗi ({e}), thử lại sau.")
                if proc is None:  # lần đầu chưa có code -> chưa chạy được
                    time.sleep(INTERVAL)
                    continue
                data = None
            if data is not None:
                h = hashlib.sha256(data).hexdigest()
                if h != last_hash:
                    print("autosync: có code mới -> cập nhật + (re)start")
                    extract_code(data)
                    last_hash = h
                    proc = restart(proc)
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        if proc:
            proc.terminate()
        print("\nautosync: dừng.")


if __name__ == "__main__":
    main()

"""
Tự đồng bộ code từ GitHub rồi restart server.
Chạy CÁI NÀY thay vì server.py trên máy AI:  python autosync.py

Vòng lặp: fetch GitHub mỗi INTERVAL giây -> có commit mới -> git pull --ff-only -> restart server.py.
Không cần webhook/cổng vào (chỉ gọi ra GitHub). ComfyUI job đang chạy không bị ảnh hưởng
(chúng nằm trong queue ComfyUI, tách rời server này).
"""
import os
import subprocess
import sys
import time

INTERVAL = int(os.environ.get("SYNC_INTERVAL", "60"))
HERE = os.path.dirname(os.path.abspath(__file__))


def git(*args):
    return subprocess.run(["git", "-C", HERE, *args], capture_output=True, text=True)


def head():
    return git("rev-parse", "HEAD").stdout.strip()


def start_server():
    return subprocess.Popen([sys.executable, "server.py"], cwd=HERE)


def restart(proc):
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    time.sleep(2)  # nhả cổng
    return start_server()


def main():
    if git("rev-parse", "--is-inside-work-tree").returncode != 0:
        sys.exit("Thư mục này chưa phải git repo. Clone repo từ GitHub rồi chạy lại (xem README-webapp.md).")

    proc = start_server()
    last = head()
    print(f"autosync: đang chạy, poll GitHub mỗi {INTERVAL}s. HEAD={last[:8]}")
    try:
        while True:
            time.sleep(INTERVAL)
            if git("fetch", "--quiet").returncode != 0:
                print("autosync: fetch lỗi (mạng?), thử lại sau.")
                continue
            remote = git("rev-parse", "@{u}").stdout.strip()
            if remote and remote != last:
                print(f"autosync: có code mới {remote[:8]} -> pull + restart")
                pull = git("pull", "--ff-only", "--quiet")
                if pull.returncode != 0:
                    print("autosync: pull lỗi (lịch sử phân nhánh?), bỏ qua:\n" + pull.stderr.strip())
                    continue
                proc = restart(proc)
                last = head()
    except KeyboardInterrupt:
        proc.terminate()
        print("\nautosync: dừng.")


if __name__ == "__main__":
    main()

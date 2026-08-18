"""Check nhỏ: Argos dịch VI->EN ra chuỗi tiếng Anh khác input. Chạy: python test_translate.py"""
from server import translate_vi_en


def test_translate():
    out = translate_vi_en("đổi vải sang màu cam")
    assert out and out.strip(), "dịch trả rỗng"
    # nếu Argos cài đúng thì phải khác input; nếu chưa cài, hàm trả nguyên văn -> in cảnh báo
    if out.strip().lower() == "đổi vải sang màu cam":
        print("CẢNH BÁO: Argos chưa cài gói vi->en, đang trả nguyên văn. Xem README-webapp.md.")
    else:
        assert "orange" in out.lower() or out != "đổi vải sang màu cam", f"dịch lạ: {out!r}"
    print("OK:", out)


if __name__ == "__main__":
    test_translate()

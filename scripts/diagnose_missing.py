"""Diagnose why certain AT commands are missed by the extractor."""
import re
import subprocess
from pathlib import Path

TARGETS = ["AT+CEXTBUT", "AT+FTPMOD", "AT+FTSIZE", "AT+CMMSSENDCF",
           "AT+CN", "AT+CAND", "AT+DLYRI", "AT+HTTPGETHEAD"]

COMMAND_RE = re.compile(r"AT\+[A-Z][A-Z0-9_]{1,60}")

def extract_pdf(path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    return result.stdout or ""

def main():
    raw_dir = Path("data/raw")
    for v in ("1.01", "1.10", "1.12"):
        pdf = raw_dir / f"SIM800 Series_AT Command Manual_V{v}.pdf"
        print(f"\n{'='*60}\n=== V{v} === ({pdf.name})\n{'='*60}")
        text = extract_pdf(pdf)
        print(f"طول متن: {len(text):,} کاراکتر")

        # تست وجود هر دستور در متن خام
        for target in TARGETS:
            count = text.count(target)
            if count == 0:
                continue
            print(f"\n▶ {target}: {count} بار در متن خام")
            # نمایش بایت‌های اطراف اولین occurrence
            idx = text.find(target)
            context = text[max(0, idx-20):idx+50]
            print(f"  context repr: {context!r}")
            # تست regex
            if target in COMMAND_RE.findall(text):
                print(f"  ✅ regex گرفت")
            else:
                print(f"  ❌ regex نگرفت ← این مشکل است")

if __name__ == "__main__":
    main()
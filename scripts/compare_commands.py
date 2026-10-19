"""Compare original vs rebuilt commands dataset to find gaps."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_commands(path: Path, key_field: str = "command") -> set:
    names = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            # امتحان چند فیلد رایج
            for k in (key_field, "name", "id", "at_command", "cmd"):
                if k in obj and isinstance(obj[k], str):
                    names.add(obj[k].strip())
                    break
    return names

def main():
    original = load_commands(ROOT / "dataset" / "commands.jsonl")
    rebuilt  = load_commands(ROOT / "dataset_after_rebuild_low_quality" / "commands.jsonl")

    print(f"دیتاست اصلی:     {len(original):>5} دستور یکتا")
    print(f"دیتاست بازسازی:  {len(rebuilt):>5} دستور یکتا")
    print(f"مشترک:           {len(original & rebuilt):>5}")
    print(f"فقط در اصلی:     {len(original - rebuilt):>5}  ← جاافتاده‌ها")
    print(f"فقط در بازسازی:  {len(rebuilt - original):>5}")

    missing = sorted(original - rebuilt)
    extra   = sorted(rebuilt - original)

    print("\n=== ۵۰ دستور اول که در بازسازی جا افتاده ===")
    for name in missing[:50]:
        print(f"  {name}")

    print("\n=== ۳۰ دستور که فقط در بازسازی هست (مشکوک) ===")
    for name in extra[:30]:
        print(f"  {name}")

    # دسته‌بندی جاافتاده‌ها
    prefixes = {}
    for name in missing:
        if name.startswith("AT+"):
            prefixes["AT+ (گرفته نشده!)"] = prefixes.get("AT+ (گرفته نشده!)", 0) + 1
        elif name.startswith("AT"):
            # پیدا کردن پیشوند AT + حرف بعدی
            key = name[:3] if len(name) >= 3 else name
            prefixes[key] = prefixes.get(key, 0) + 1
        else:
            prefixes["غیر AT"] = prefixes.get("غیر AT", 0) + 1

    print("\n=== دسته‌بندی جاافتاده‌ها ===")
    for k, v in sorted(prefixes.items(), key=lambda x: -x[1]):
        print(f"  {k:>20}: {v}")

    # ذخیره لیست کامل برای بررسی
    out = ROOT / "dataset_after_rebuild_low_quality" / "missing_commands.txt"
    out.write_text("\n".join(missing), encoding="utf-8")
    print(f"\nلیست کامل جاافتاده‌ها ذخیره شد در: {out}")

if __name__ == "__main__":
    main()
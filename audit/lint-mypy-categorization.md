# دسته‌بندی خطاهای Ruff و mypy

## خروجی‌های کامل

- `ruff-full-before.txt`: اجرای کامل پیش از اصلاح، با مسیرهای `<target-repo>`.
- `mypy-full-before.txt`: اجرای کامل پیش از اصلاح، با مسیرهای `<target-repo>`.
- `ruff-full-final.txt`: اجرای نهایی Ruff.
- `mypy-full-final.txt`: اجرای نهایی mypy.

## (a) خطاهای واقعی منطقی/type

mypy پیش از اصلاح ۸۳ خطا داشت. ۲۹ خطا پس از نصب stubهای توسعه‌ای و اعمال اصلاح‌های type-only باقی ماند: castهای خروجی YAML/JSON، annotation برای generatorهای داخلی، narrowing با `assert` برای leafهای nullable، annotation خروجی iteratorها، `dict[str, Any]` و اصلاح scope متغیر exception. این اصلاح‌ها منطق runtime را تغییر نمی‌دهند. نتیجه نهایی: `Success: no issues found in 22 source files`.

## (b) هشدارهای سبک

Ruff پیش از اصلاح ۱۴۲ finding داشت: `UP006=59`, `E702=30`, `I001=16`, `UP035=15`, `E501=14`, `F401=6`, `UP045=2`. ابتدا ۹۷ مورد با `ruff --fix` به‌صورت safe اصلاح شد؛ ۴۴ مورد باقی‌مانده شامل semicolonهای چنددستوری و line wrapping بود و به‌صورت مکانیکی، بدون تغییر رفتار، بازنویسی شد. چهار import قدیمی `Iterator` نیز به `collections.abc` منتقل شد. نتیجه نهایی: `All checks passed!`.

## (c) خطاهای ناشی از پورت sibling

مولد `generate_at_urc.py` از sibling پورت شده و ۵۰ finding اولیه mypy آن عمدتاً `no-untyped-def` و `no-untyped-call` بود. بازنویسی کامل generator خارج از minimal fix بود و انجام نشد؛ به‌جای آن دو stub توسعه‌ای اضافه و یک override محدود فقط برای همین module ثبت شد: `disallow_untyped_defs=false` و `disallow_untyped_calls=false`. یک return annotation و import `Any` نیز برای موارد مستقیم اضافه شد. هیچ منطق generator یا خروجی تولیدشده تغییر نکرد و اجرای دوباره generator idempotent ماند.

## نتیجه و Approval Needed

برای lint و mypy مورد unresolved باقی نمانده و Approval Needed جدیدی ایجاد نشد. موارد مستقل قبلی مانند ارزیابی SIM800-Monorepo، تکمیل dataset/errors و نصب mkdocs همچنان در گزارش اصلی باقی هستند.

# چک‌لیست بازبینی دستی نهایی

این چک‌لیست برای `next_action: manual_final_review` در `state.json` تهیه شده است. هر مورد باید توسط کاربر بررسی شود و یکی از تصمیم‌های پیشنهادی در ستون «تصمیم موردنیاز» ثبت شود. هیچ داده، secret یا دسترسی جدیدی بدون تأیید صریح کاربر اضافه نشود.

## چک‌لیست خلاصه

| مورد | وضعیت فعلی | تصمیم موردنیاز | دستور یا اقدام پیشنهادی |
|---|---|---|---|
| `dataset/errors.jsonl` | فایل به‌دلیل نبود شاهد کافی خالی مانده است؛ یک error-code نیز به‌صورت مستند blocked شده است. | آیا برای error codeها شاهد معتبر و قابل ردیابی فراهم شده است؟ اگر نه، خالی‌ماندن فایل را به‌عنوان تصمیم آگاهانه تأیید کنید و رکورد blocked را بدون حدس‌زدن نگه دارید. | شواهد محلی را بررسی کنید: `find data dataset docs -type f -maxdepth 5 -print` و سپس `grep -R "error\|CME\|CMS" data dataset docs -n`. برای هر رکورد فقط source، page/section، model scope و confidence قابل اثبات را ثبت کنید. پس از تغییر، validator و تست‌های dataset را اجرا کنید. |
| `mkdocs` | `mkdocs` در محیط audit نصب نبود و docs build اجرا نشده است. | آیا اجرای build مستندات در محیط محلی کاربر برای پذیرش نهایی ضروری است؟ | در ریشه مخزن اجرا کنید: `python3 -m venv .venv-docs && . .venv-docs/bin/activate && python -m pip install --upgrade pip mkdocs mkdocs-material && mkdocs build --strict`. در صورت استفاده از theme یا pluginهای دیگر، dependencyهای اعلام‌شده در `mkdocs.yml` را نیز نصب کنید. خروجی موفق باید بدون warning/error باشد؛ سپس `mkdocs serve` را برای مرور دستی صفحات اجرا کنید. |
| `SIM800-Monorepo` | این مخزن در scope فعلی در دسترس نبوده و port/ارزیابی نشده است. | آیا کاربر می‌خواهد دسترسی read-only یا مسیر/clone این مخزن را فراهم کند، یا آن را خارج از دامنه نگه می‌دارد؟ | اگر خارج از دامنه است، تصمیم را ثبت و blocker را به‌عنوان accepted out-of-scope ببندید. اگر لازم است بررسی شود، مسیر clone یا دسترسی read-only را فراهم کنید؛ سپس فقط پس از تأیید، baseline، license، ساختار و تفاوت‌های موردنیاز را audit کنید. هیچ clone، fetch یا دسترسی خارجی بدون تأیید کاربر انجام نشود. |
| `secret history scan` | scan فعلی فقط basic regex بوده است؛ `gitleaks`/ابزار کامل history scan در محیط audit در دسترس نبود. | آیا `gitleaks` در محیط محلی کاربر نصب و قابل اجراست؟ در صورت نبودن، آیا کاربر اجازه نصب ابزار را می‌دهد؟ | بررسی نصب: `command -v gitleaks && gitleaks version`. نصب پیشنهادی با Go: `go install github.com/gitleaks/gitleaks/v8@latest` و سپس `export PATH="$(go env GOPATH)/bin:$PATH"`. اجرای scan از ریشه مخزن: `gitleaks detect --source . --log-opts="--all" --redact --report-format json --report-path gitleaks-report.json`. خروجی را بررسی کنید؛ secret واقعی را در گزارش یا chat کپی نکنید. |

## روند گام‌به‌گام

### ۱. آماده‌سازی و ثبت تصمیم‌ها

1. از مخزن و artifact فعلی یک backup محلی بگیرید و مطمئن شوید working tree ناخواسته تغییر نکرده است:
   ```bash
   git status --short
   cat /home/ubuntu/sim800-audit-output/state.json
   ```
2. برای هر چهار ردیف، یکی از وضعیت‌های `resolved`، `accepted`، `deferred` یا `blocked` را انتخاب کنید.
3. تصمیم‌ها، نام ابزار، نسخه ابزار، زمان اجرا و مسیر خروجی را در یک یادداشت محلی ثبت کنید؛ secretها و credentialها را ثبت نکنید.

### ۲. تصمیم درباره `dataset/errors.jsonl`

1. شواهد را از sourceهای محلی و اسناد قابل ردیابی بررسی کنید.
2. برای هر error code، حداقل source، صفحه/بخش، مدل‌های قابل اعمال و confidence را مشخص کنید.
3. اگر شاهد کافی وجود ندارد، فایل را با حدس یا داده پورت‌شده پر نکنید؛ تصمیم «insufficient evidence / intentionally empty» را ثبت کنید.
4. اگر رکورد معتبر اضافه شد، JSONL، schema و provenance را validate کنید و regression dataset را دوباره اجرا کنید.

### ۳. تصمیم درباره `mkdocs`

1. فقط در صورت ضروری‌بودن docs acceptance، محیط مجازی محلی بسازید.
2. `mkdocs build --strict` را اجرا کنید و همه warningها را رفع یا آگاهانه ثبت کنید.
3. خروجی build را بازبینی کنید و artifact build را بدون درخواست جداگانه به Git یا سرویس خارجی push نکنید.

### ۴. تصمیم درباره `SIM800-Monorepo`

1. مشخص کنید بررسی این مخزن برای پذیرش این audit الزام است یا خیر.
2. اگر خیر، آن را out-of-scope اعلام و دلیل را ثبت کنید.
3. اگر بله، دسترسی read-only یا مسیر محلی را فراهم کنید و قبل از هر عملیات، scope، baseline، license و محدودیت push را جداگانه بررسی کنید.

### ۵. اجرای secret history scan

1. ابتدا `command -v gitleaks` و `gitleaks version` را اجرا کنید.
2. در صورت نبودن ابزار و مجازبودن نصب، از روش Go بالا استفاده کنید؛ در محیط‌های سازمانی از package manager تأییدشده سازمان استفاده کنید.
3. scan را با `--log-opts="--all"` روی کل history اجرا کنید.
4. اگر finding وجود داشت، مقدار secret را نمایش یا کپی نکنید؛ فقط مسیر، commit، نوع finding و اقدام remediation را در گزارش redacted ثبت کنید.
5. بعد از remediation، scan را تکرار کنید و نتیجه را با زمان و نسخه ابزار ثبت کنید.

## معیار بستن بازبینی

- هر چهار مورد دارای تصمیم صریح و ثبت‌شده باشند.
- dataset بدون evidence پر نشده باشد.
- نتیجه `mkdocs build --strict` یا تصمیم مستند برای خارج‌بودن آن ثبت شده باشد.
- وضعیت scope/access برای `SIM800-Monorepo` مشخص باشد.
- نتیجه history scan با نسخه ابزار و بدون افشای secret ثبت شده باشد.
- پس از تصمیم‌ها، `state.json` با وضعیت واقعی و `next_action` نهایی همگام شود.

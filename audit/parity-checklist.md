# چک‌لیست پاریتی

| Capability | Source | Status | Target Equivalent | Note |
|---|---|---|---|---|
| 18 فایل dat_01 تا dat_18 | sim800l-data-16 | covered | dataset/*.jsonl | ۱ رکورد blocked رد شد و ثبت شد |
| AT/URC، ۹ ماژول | sim800-at-urc | covered | data/at_urc و generated/cpp | generator روش B، smoke compile موفق |
| ۹ مدل | sim800-capabilities | covered | data/capabilities/models | validate موفق |
| ۱۳ دسته داخل محدوده | sim800-capabilities | covered | data/capabilities | هر FieldValue دارای status/source_id/source_ref/confidence |
| ۱۰ دسته خارج محدوده | sim800-capabilities | covered | data/capabilities/out-of-scope.yaml | با دلیل منبع حفظ شد |
| Schemaهای قابلیت | sim800-capabilities | covered | data/capabilities/schema | provenance sidecar |
| CLI قابلیت‌ها | sim800-capabilities | covered | sim800 capabilities | validate/list/show/find تست شد |
| SIM800-Monorepo | خارج از دامنه | blocked | None | دسترسی ارزیابی نشد |

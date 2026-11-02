# Listenify — lokal implementatsiya va tekshiruv holati

## GitHub preparation update — 2026-11-02

The earlier notes below describe the initial local implementation. During the subsequent GitHub preparation pass:

- The recording query was changed to lock only the recording row, avoiding PostgreSQL's nullable-join restriction. Uploads are now limited while the multipart stream is parsed, and listening attempts have a session-scoped cancellation endpoint and stale-attempt expiry.
- Repeated per-row database queries in the user and material lists were reduced; large lists still need pagination and load testing.
- A temporary local PostgreSQL 17 instance was used to run **37 backend and concurrency tests successfully**, including recording media/submit/delete, access changes after group transfers, and concurrent starts, finishes, and reviews.
- **4 Chromium end-to-end tests passed against PostgreSQL**, including synthetic microphone recording, upload, submission, grading, group restrictions, seek handling, and cancellation on navigation.
- These browser tests used a synthetic microphone. Physical microphones, Firefox, Safari/WebKit, and a remote GitHub Actions run remain unverified. SMTP, public hosting, backup, and the cleanup scheduler still require production configuration.
- The source code is MIT licensed. Rights to the supplied logo and photographic assets have not been independently verified.

Sana: 2026-11-02, Asia/Tashkent.

## Amalga oshirilgan

- Django 5.2 / React / TypeScript ilovasi, SQLite lokal bazasi va PostgreSQL konfiguratsiyasi.
- Email/parol orqali hisob yaratish va kirish, parol tiklash, server sessiyalari, CSRF va asosiy tezlik cheklovi; birinchi admin boshqaruv buyrug‘i orqali yaratiladi.
- Guruhlar, bir nechta o‘quvchini yaxlit ko‘chirish, shaxsiy/guruh daraja cheklovlari, bloklash, sessiyalarni bekor qilish va hisob o‘chirish.
- Audio yuklash, ffprobe yordamida format va davomiylikni tekshirish, versiyalar, e’lon qilish/arxivlash, skript va ruxsat tekshiriladigan fayl oqimi.
- Ijro vaqti/interval/real vaqtga asoslangan server hisoblagichi; takroriy finish va parallel start uchun tranzaksiya va cheklovlar.
- Browser MediaRecorder, qayta tinglash, upload retry va idempotency; shaxsiy yozuvlarni saqlash, alohida yuborish va baholash.
- Admin audio, guruh, o‘quvchi, yozuv navbati, baholash va audio versiyasi bo‘yicha tinglash natijalari; revision orqali eskirgan bahoni rad etish.
- Foydalanuvchi tasdiqlagan logo va suratlar, Photo Glass yo‘nalishi, mobil layout, harakat/shaffoflikni kamaytirish.
- Yopiq media faylini o‘chirish tranzaksiya yakunlangach boshlanadi; xatolar DB navbatiga yozilib keyingi cleanup ishida qayta uriniladi.

Kod jismonan bitta Django `core` ilovasida: `models`, `policy`, `listening`, `media`, `serializers`, `views` va migratsiyalar. U texnik reja tasvirlagan alohida Django ilovalariga bo‘linmagan; ajratilgan mas’uliyatlar ushbu modullar orqali ifodalangan.

## O‘tkazilgan tekshiruvlar

- `manage.py check` va `makemigrations --check --dry-run`: muvaffaqiyatli.
- Backend: 25 ta test muvaffaqiyatli. Tinglash chegaralari, uzun pauza, seek, version, idempotency, sessiya/bloklash, huquqlar, guruh ko‘chirish, fayl va baholash holatlari tekshirildi.
- PostgreSQL qator qulflari uchun 3 ta test mavjud, lekin lokal kompyuterda PostgreSQL topilmagani sababli **o‘tkazib yuborildi**. SQLite ularning o‘rnini bosmaydi.
- React TypeScript build: muvaffaqiyatli. `npm audit --omit=dev` tekshiruvida zaiflik topilmadi.
- Chromium: 3 ta brauzer testi muvaffaqiyatli. Ro‘yxatdan o‘tish, admin audio yuklashi, guruh/cheklov, to‘liq tinglash va qayta tinglash, seek rad etilishi, mikrofon yozish → upload → submit → admin bahosi → o‘quvchiga ko‘rinishi, mobil kenglik tekshirildi.
- Browser mikrofon tekshiruvi Chromium sun’iy media qurilmasi bilan bajarildi. Skrinshotlardagi test hisoblari va audio faqat vaqtinchalik test bazasida bo‘lgan; haqiqiy lokal bazaga demo ma’lumot kiritilmagan.

## Relizdan oldin qolgan ishlar

- PostgreSQL o‘rnatib yoki servisga ulab, domain, concurrency va browser testlarini qayta bajarish. GitHub Actions konfiguratsiyasi qo‘shilgan, lekin ushbu sessiyada remote CI ishlatilmagan.
- Jismoniy mikrofon va boshqa qurilmalarda, jumladan Firefox va Safari/WebKit’da format va permission oqimini qo‘lda sinash.
- HTTPS hosting, doimiy yopiq disk, backup/restore, cleanup scheduler va ishlaydigan SMTP’ni tanlash va sozlash. Hozir lokal email rejimi faqat terminalga havola chiqaradi.
- Lokal fayl tizimi yopiq saqlash sifatida amalga oshirilgan; S3-compatible storage adapteri hali ulanmagan. Bir nechta ilova serverida umumiy doimiy storage alohida sozlanishi kerak.
- Katta auditoriyaga chiqarishdan avval access, media hajmi, yuklama va xavfsizlikni ishlab chiqarish muhitida tekshirish.

Ushbu holat ishlaydigan lokal mahsulot poydevori va asosiy oqimlarni bildiradi. Yuqoridagi muhit va brauzer tekshiruvlari bajarilmaguncha ishlab chiqarishga tayyor reliz deb hisoblanmaydi.

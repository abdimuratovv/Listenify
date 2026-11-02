# Listenify — joriy holat va kod review

> Historical review: the PostgreSQL nullable-join query, streaming upload limits, attempt cancellation, and repeated list queries identified below were subsequently addressed in the working tree. See the root README and latest validation notes for the current verification state.

Sana: 2026-11-02, Asia/Tashkent. Ko‘lam: ishchi papkadagi barcha joriy mahsulot kodlari, mavjud spetsifikatsiya va testlar. Bu review; mahsulot kodiga o‘zgartirish kiritilmadi.

## Umumiy baho

Listenify’ning asosiy foydalanuvchi va admin oqimlari lokal prototip/MVP implementatsiyasi sifatida yaratilgan. Dastur lokal SQLite bazasi bilan ishlaydi; haqiqiy foydalanishga chiqarishdan oldin quyida ko‘rsatilgan PostgreSQL va upload muammolarini bartaraf etish, keyin reliz muhitini va qurilmalarni tekshirish kerak. Hozirgi holatni ishlab chiqarishga tayyor deb baholash mumkin emas.

## Amalga oshirilgan qismlar

| Yo‘nalish | Holat |
| --- | --- |
| Hisoblar | Email/parol bilan ro‘yxatdan o‘tish, kirish, parol tiklash oqimi, DB sessiyalar, CSRF, bloklash va admin bootstrap |
| Guruhlar va darajalar | Guruh yaratish/tahrirlash, bir nechta o‘quvchini ko‘chirish, shaxsiy va guruh cheklovlari |
| Audiolar | Yuklash, ffprobe tekshiruvi, skript, daraja, qoralama/e’lon/arxiv, versiyalar, yopiq audio oqimi |
| Tinglashlar | Server urinishlari, vaqt/interval tekshiruvi, qayta finishni takror hisoblamaslik, shaxsiy natijalar |
| Yozuvlar | MediaRecorder bilan yozish va preview, upload retry, shaxsiy ro‘yxat, ixtiyoriy yuborish |
| Admin | Materiallar, foydalanuvchilar, guruhlar, yozuvlar, baho/izoh, revision bilan tahrir to‘qnashuvi, tinglash natijalari |
| Vizual | Tasdiqlangan logo manbasi, vinil/kasseta fonlari, glass interfeys, moslashuvchan layout va kam harakat/shaffoflik sozlamasi |

## Review natijalari

### P1 — PostgreSQL’da yozuvni tinglash, yuborish va o‘chirish ishlamasligi

[`backend/core/views.py:247`](../../backend/core/views.py#L247) dagi so‘rov `select_for_update()` ni ixtiyoriy `review` munosabatiga `select_related()` bilan qo‘llaydi. Ushbu so‘rovdagi `review` haqiqatan `LEFT OUTER JOIN` sifatida yaratilishi ko‘rildi. Django/PostgreSQL bu nullable join tomoniga odatiy `FOR UPDATE` qo‘llashni qo‘llab-quvvatlamaydi; natijada recording media, submit va delete yo‘llari server xatosiga duch keladi. Lokal SQLite buni ko‘rsatmaydi, chunki u `select_for_update()` ni bajarmaydi. PostgreSQL serveri mavjud bo‘lmagani uchun xato shu muhitda ishga tushirib tasdiqlanmagan; bu SQL tuzilmasi va [Django hujjatiga](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update) asoslangan xulosa.

**Tavsiya:** recording qatorini alohida qulflash yoki PostgreSQL’da `select_for_update(of=('self',))` ishlatish; audio oqimi, submit va delete’ni haqiqiy PostgreSQL integratsiya testlariga qo‘shish.

### P1 — Upload hajmi qabul qilish vaqtida chegaralanmagan

[`backend/core/views.py:223`](../../backend/core/views.py#L223) dagi `request.POST`/`request.FILES` multipart yuklashni parse qiladi; [`backend/core/media.py:23`](../../backend/core/media.py#L23) dagi 50/100 MiB limit shundan keyin tekshiriladi. [`backend/config/settings.py:64`](../../backend/config/settings.py#L64) dagi `DATA_UPLOAD_MAX_MEMORY_SIZE` upload fayllarini hisoblamaydi; `FILE_UPLOAD_MAX_MEMORY_SIZE` esa qat’iy hajm limiti emas, diskka ko‘chirish chegarasi. Shuning uchun ro‘yxatdan o‘tgan foydalanuvchi juda katta upload bilan vaqtinchalik disk va server resurslarini band qilishi mumkin. [Django sozlamalari hujjati](https://docs.djangoproject.com/en/5.2/ref/settings/#data-upload-max-memory-size).

**Tavsiya:** reverse proxy’da request-body chegarasini va serverda oqim davomida to‘xtatadigan upload handlerini qo‘llash; katta va noma’lum uzunlikdagi uploadlar bilan test qilish.

### P2 — Sahifa yopilganda tugallanmagan urinish serverda bekor qilinmaydi

[`frontend/src/useListening.ts:118`](../../frontend/src/useListening.ts#L118) cleanup’i faqat mijozdagi ID’ni o‘chiradi. Serverda esa [`backend/core/listening.py:18`](../../backend/core/listening.py#L18) orqali yangi urinish boshlangandagina avvalgi faol urinish bekor qilinadi. Shu sabab eski satr DB’da `active` qolishi mumkin. Odatdagi refresh’da frontend eski ID’ni davom ettirmaydi, ammo bu spetsifikatsiyadagi server tomonida bekor qilish talabi bilan aynan mos emas; ayniqsa pauzadagi urinish uchun timeout qat’iy emas.

**Tavsiya:** sessiyaga bog‘langan bekor qilish endpointi va sahifadan chiqishda best-effort signal, shuningdek serverda eskirgan urinishlar muddati va tekshiriladigan cleanup qo‘shish.

### P2 — Ro‘yxatlarda so‘rovlar soni ma’lumot bilan chiziqli o‘sadi

[`backend/core/views.py:281`](../../backend/core/views.py#L281) foydalanuvchilar uchun har bir qatorda qo‘shimcha count va cheklov so‘rovlarini bajaradi; [`backend/core/serializers.py:13`](../../backend/core/serializers.py#L13) har bir material uchun tinglash sonini alohida izlaydi. Ro‘yxatlar sahifalanmagan. O‘quvchi yoki material ko‘payganda admin oynasi sekinlashishi va DB yuklamasi ortishi mumkin.

**Tavsiya:** `annotate`/`prefetch_related` orqali so‘rovlarni birlashtirish va ro‘yxatlarga server pagination qo‘shish; hajmli ma’lumot bilan profiling o‘tkazish.

## Tekshiruvlar va muhit

- Ushbu review vaqtida backend domain testlari qayta ishga tushirildi: **25 ta muvaffaqiyatli**, PostgreSQL talab qiladigan **3 ta test o‘tkazib yuborilgan**.
- TypeScript `tsc --noEmit` va frontend Prettier tekshiruvi muvaffaqiyatli.
- Avvalgi implementatsiya sessiyasida 3 ta Chromium end-to-end testi o‘tgan; ushbu review’da ular qayta ishlatilmadi. O‘sha testlarda sun’iy mikrofon ishlatilgan.
- Jismoniy mikrofon, Firefox/Safari/WebKit va PostgreSQL’dagi real parallel ishlash ushbu review’da tekshirilmagan. GitHub Actions fayli mavjud, lekin remote CI natijasi tasdiqlanmagan.
- Lokal server `http://127.0.0.1:8000` javob berdi. Tekshiruv paytida lokal bazada **0 hisob, 0 material, 0 yozuv** bor edi; birinchi admin va audio hali kiritilmagan.
- Lokal email reset havolasini terminalga chiqaradi; real SMTP, hosting, HTTPS, backup va cleanup scheduler ulanmagan yoki sozlangani tasdiqlanmagan.
- PostgreSQL konfiguratsiyasi mavjud; joriy lokal DB SQLite. Audio yopiq lokal diskda, alohida tashqi storage adapteri hali mavjud emas.

## Git va topshirish holati

Spetsifikatsiya va reja `d155879` commitiga kiritilgan. Mahsulot kodi, migratsiyalar, frontend, CI konfiguratsiyasi, README va dependency fayllari ishchi papkada; ko‘pchiligi Git tomonidan hali kuzatilmayapti va commit qilinmagan. `.gitignore` ham o‘zgargan. `docs/brand-exploration/` oldindan mavjud kuzatilmagan papka sifatida saqlanmoqda. Yangi checkoutga mahsulot kodini ko‘chirish uchun kerakli fayllarni alohida ko‘rib chiqib commit qilish zarur.

## Tavsiya etilgan navbat

1. PostgreSQL’dagi recording so‘rovini va upload qabul qilish chegarasini tuzatish.
2. Haqiqiy PostgreSQL’da domain, concurrent va browser testlarini ishlatish; eski urinishlarni bekor qilishni test bilan yakunlash.
3. Jismoniy mikrofon va Firefox/Safari tekshiruvlari, uzun ro‘yxatlar uchun profiling.
4. Birinchi admin va haqiqiy materiallarni sozlash; reliz uchun SMTP, HTTPS, doimiy yopiq storage, backup va cleanup monitoringini ulash.
5. Mahsulot kodini ko‘rib chiqilgan fayllar bilan Git’ga kiritish, CI va reliz tekshiruvlarini qayta bajarish.

# Listenify — texnik taklif va MVP amalga oshirish rejasi

Sana: 2026-11-02, Asia/Tashkent.
Holat: 2026-11-02 kuni tasdiqlangan; implementatsiya va tekshiruv holati validation hujjatida qayd etiladi.

## 1. Manbalar va tekshiruv natijasi

- Mahsulot talablari: `docs/superpowers/specs/2026-11-01-listenify-mvp-design.md`.
- Handoff: `D:/Downloads/LISTENIFY_NEW_CHAT.md`; repozitoriyda ham nusxa mavjud.
- Tasdiqlangan brend: `docs/brand/README.md` va `listenify-approved-reference.png`.
- Vizual yo‘nalish: `docs/superpowers/specs/visuals/listenify-photo-glass-v5.html`.
- Vinil, kasseta va glass referensi mavjud va ko‘rib chiqildi.
- Git repozitoriyda mahsulot kodi va paket manifestlari yo‘q. `docs/brand-exploration/` kuzatilmagan mavjud papka; unga tegilmaydi.
- Ishchi katalog va uning yuqori kataloglarida `AGENTS.md` topilmadi.
- Muhit: Python 3.12.10, Node.js 22.12.0, npm 10.9.0.
- Mavjud skill kataloglarida `writing-plans` topilmadi; ushbu reja bevosita tayyorlandi, bu skill ishlatildi deb hisoblanmaydi.

## 2. Texnik variantlar

| Variant | Afzallik | Xarajat / cheklov |
| --- | --- | --- |
| **Django + React/TypeScript — tavsiya** | Tayyor sessiya, parol, CSRF, ORM va migratsiyalar; media va atomar amallarni bitta server boshqaradi | Python va Node muhitlari kerak |
| Next.js + PostgreSQL + auth kutubxonasi | Bitta TypeScript tili, frontend/server umumiy loyiha | Sessiya, media, ish navbati va auth qismlarini alohida birlashtirish kerak |
| React + boshqariladigan auth/DB/storage | Infratuzilmani tez ulash mumkin | Tashqi hisob va sozlamalar kerak; tinglash tranzaksiyalari baribir server kodini talab qiladi |

Tavsiya: Python 3.12, Django 5.2 liniyasining o‘rnatish vaqtidagi xavfsizlik yangilangan patchi, React va TypeScript, Vite. Paket versiyalari implementatsiya boshlanganda registry va rasmiy moslik talablariga qarab tekshiriladi va lock fayllarga mahkamlanadi. Node 22.12.0 tanlangan Vite talabiga yetmasa Node yangilanadi yoki mos qo‘llab-quvvatlanadigan Vite tanlanadi; moslik taxmin qilinmaydi.

DB: PostgreSQL — asosiy va reliz tekshiruv muhiti. Bir kishilik dastlabki lokal ish uchun SQLite ruxsat etiladi, lekin parallel urinish/baholash kafolatlari faqat PostgreSQL testlaridan keyin qabul qilinadi. PostgreSQL lokal o‘rnatma yoki Docker orqali ishga tushiriladi; mavjudligi tekshiriladi.

Auth: alohida pulli provaydersiz Django email/parol va DB sessiyalari. Email yagona, normalizatsiya qilingan identifikator; ro‘yxatdan o‘tishda rol qabul qilinmaydi. Reset xatlari lokalda konsolga, haqiqiy muhitda SMTP orqali yuboriladi. Konsol rejimi email jo‘natildi degan da’vo bilan ko‘rsatilmaydi. Login va reset uchun tezlik cheklovi qo‘shiladi.

Media: web root tashqarisidagi yopiq lokal katalog va almashtiriladigan storage adapteri. Relizning boshlang‘ich varianti: bitta ilova serveri + PostgreSQL + doimiy yopiq disk + HTTPS reverse proxy. Hosting provayderi yoki xarid tanlanmagan. Keyingi ko‘lam uchun private S3-compatible adapter qo‘shish mumkin; dastlab tashqi storage hisobini talab qilmaydi.

## 3. Tuzilma va modul chegaralari

```text
backend/
  config/       sozlamalar, URL, muhit
  accounts/     email auth, sessiyalar, hisob holati
  classrooms/   guruhlar, ko‘chirish, cheklovlar
  library/      material va o‘zgarmas versiyalar
  listening/    urinishlar, interval algoritmi, natijalar
  recordings/   yuklash, egasi, yuborish holati
  reviews/      baho, izoh, parallel tahrir nazorati
  mediafiles/   yopiq oqim, fayl tekshiruvi, tozalash navbati
frontend/
  src/app/      navigatsiya, sessiya, umumiy API klient
  src/features/ library, player, recorder, records, admin
  src/ui/       glass, dialog, status, fokus, accessibility
docs/plans/
```

Joriy implementatsiyada Django ilovalari alohida kataloglarga emas, bitta `backend/core` ichidagi mas’ul modullarga ajratilgan. Brauzer va API bir origin orqali ishlaydi; developmentda Vite `/api` so‘rovlarini Django’ga proxy qiladi. HttpOnly sessiya cookie, HTTPSda Secure, SameSite=Lax va CSRF token ishlatiladi. Auth tokenlari localStorage’da saqlanmaydi. Barcha mutationlar CSRF va serverdagi huquq tekshiruvidan o‘tadi. Foydalanuvchi kiritgan skript/izoh HTML sifatida bajarilmaydi.

Django ichki boshqaruvi mahsulotdagi admin interfeysini almashtirmaydi. Bootstrap admin terminal buyrug‘i orqali yaratiladi; standart ochiq parol va public admin yaratish endpointi bo‘lmaydi. Mahsulot adminlarining vakolati bir xil.

## 4. Ma’lumotlar modeli

| Model | Asosiy ma’lumot va invariant |
| --- | --- |
| User | UUID, email unique, ism, parol hash, role, active, session_generation, nullable current_group |
| Session | Django DB sessiyasi; user identifikatori va generation |
| Classroom | UUID, nom, yaratilgan vaqt |
| PersonalLevelBlock | user + level unique |
| GroupLevelBlock | group + level unique |
| Material | sarlavha, tavsif, draft/published/archived, current_version |
| MaterialVersion | material + version_number unique, level, script, private file, server o‘lchagan duration; e’lon qilingach o‘zgarmas |
| ListeningAttempt | user, version, UUID, active/completed/cancelled, event sequence, server vaqtlari, tekshirilgan intervallar va ijro vaqti |
| ListeningResult | user + version unique, completed_count |
| Recording | user, version, private file, duration, saved/submitted/graded, revision, upload idempotency key |
| Review | recording unique, 1–5 score, majburiy comment, original reviewer/time, last editor/time, revision |
| FileCleanupJob | private key, urinishlar soni, next_attempt_at, xato; DB commitdan keyin qayta bajariladigan tozalash |

`current_group` bitta FK bo‘lgani uchun o‘quvchi bir vaqtda bitta guruhda bo‘ladi. Bu tizim a’zolarning tarixiy guruh hisobotini va’da qilmaydi. Natijalar guruhga emas user/versionga bog‘lanadi. Ko‘chirish userlar qatorini qulflab bitta tranzaksiyada bajariladi; maqsad guruh va tanlangan barcha userlar avval tekshiriladi.

Baholovchi hisob o‘chirilsa review’dagi FK nullable bo‘ladi, auditdagi admin nomi nusxasi saqlanadi; boshqa o‘quvchilarning baholari kaskad bilan yo‘qolmaydi. O‘chirilayotgan o‘quvchining o‘z natijalari va yozuv metadata’si o‘chiriladi.

## 5. Serverdagi kirish qoidalari

- Har so‘rovda sessiya, active holat va session_generation tekshiriladi. Bloklash generation’ni oshiradi; eski sessiyalar unblockdan keyin ham yaroqsiz qoladi.
- Samarali yopiq darajalar: personal blocks UNION current group blocks.
- Kutubxona, skript, media byte range, urinish yaratish/yakunlash va yozuvni saqlash ayni access policy’dan foydalanadi.
- O‘quvchi media faylini faqat autentifikatsiyalangan endpoint orqali oladi; public MEDIA_URL marshruti yaratilmaydi. Javoblar private/no-store, Range/206 va noto‘g‘ri range uchun 416 bilan ishlaydi.
- Yopilgan/arxivlangan manba o‘quvchiga yangi mashq uchun ochilmaydi. O‘z saqlangan yozuviga kirish saqlanadi. Admin baholash uchun eski version audio va skriptga kira oladi.
- O‘quvchi boshqaning yozuvi yoki statistikasi uchun UUID almashtirsa kirish rad etiladi. Admin amallari faqat server tasdiqlagan rolda ishlaydi.
- Submission eski yozuvni tekshiruvga yuborishdir: manbaning keyinchalik yopilishi oldin saqlangan yozuvni yo‘qotmaydi; yangi yozuv yaratish esa taqiqlanadi.

## 6. Tinglash protokoli

1. Player boshidan ijro uchun serverdan attempt oladi. User/versionga tegishli barcha startlar bir xil DB qulfi ostida ketma-ketlashtiriladi; yangi attempt avvalgisini bekor qiladi.
2. Client har 1 soniyada va play/pause/seeking/waiting/ended hodisalarida tartib raqamli heartbeat yuboradi. Bir vaqtda bitta so‘rov; tez hodisalar navbatga qo‘yiladi. Attempt user va sessiyaga bog‘lanadi.
3. Server oxirgi qabul qilingan media nuqtasi va monotonic vaqt o‘rnini bosadigan server qabul vaqti bilan delta’ni tekshiradi. Faqat ketma-ket odatiy ijrodagi interval tasdiqlanadi. Seeking, pause va buffering oralig‘i qo‘shilmaydi. Qayta yoki tartibsiz sequence ijro vaqtini oshirmaydi.
4. Tolerans har heartbeatga berilmaydi. Urinish davomida media qamrovi yetishmovchiligining jami <= 0.25 s va tekshirilgan ijro vaqti >= duration - 0.25 s bo‘lishi shart. Intervallar birlashtiriladi; orqaga qayta tinglash ijro vaqtini oshirishi mumkin, lekin qamrovni ikki marta oshirmaydi.
5. Server qabul vaqti ijro tezligining yuqori chegarasini tekshiradi; ruxsat etilgan kechikish qamrovga bepul soniyalar qo‘shmaydi. Heartbeat oralig‘i 5 soniyadan oshsa attempt bekor qilinadi. Network xatosida client urinishni hisoblanmaydigan holatga o‘tkazadi va foydalanuvchiga qayta boshidan boshlash kerakligini ko‘rsatadi.
6. `finish` qamrov, yetarli tasdiqlangan vaqt, media yakuni, active attempt va joriy accessni tekshiradi. Attempt completed va count +1 bir tranzaksiyada; takroriy finish mavjud yakunni qaytaradi.
7. Refresh/unmount yangi urinishni talab qiladi. Page exit cancel best-effort; serverdagi eskirish va yangi start bekor qilishi ham ishlaydi. Brauzer qayta ochilganda eski attempt davom ettirilmaydi.

Bu protokol client da’volarini vaqt/holat bilan tekshiradi; insonning diqqatini yoki soxtalashtirilgan clientni mutlaq aniqlashni va’da qilmaydi. Tarmoq kechikishi uchun xavfsiz rad etish holatlari UI’da tushuntiriladi.

## 7. Yozish, yuklash va baholash

`getUserMedia` + `MediaRecorder`; brauzer qo‘llaydigan WebM/Opus yoki MP4 format feature detection orqali tanlanadi. HTTPS yoki localhost zarur. Record bosilganda original audio pauza bo‘ladi. Stopdan keyin lokal Blob preview, qayta yozish va save mavjud. Sahifadan chiqishda saqlanmagan Blob haqida ogohlantirish beriladi; media tracklar va object URLlar tozalanadi.

Boshlang‘ich limitlar: material audio 100 MiB / 30 daqiqa, ovoz yozuvi 50 MiB / 10 daqiqa. Limitlar server konfiguratsiyasida; UI ham ko‘rsatadi. Server kengaytmaga ishonmaydi: format, fayl hajmi va davomiylik ffprobe orqali tekshiriladi; noto‘g‘ri yoki qo‘llanmaydigan fayl rad etiladi. ffprobe mavjudligi setupda tekshiriladi. Saqlash vaqtida access yana tekshiriladi.

Upload avval vaqtinchalik yopiq joyga yoziladi; muvaffaqiyatli tekshiruv va DB saqlashdan keyingina saved qaytariladi. Idempotency key upload retry’da dublikat yozuvni oldini oladi; xuddi shu key bilan boshqa fayl conflict bo‘ladi. Xatoda Blob saqlanadi va retry mumkin. DBga bog‘lanmagan vaqtinchalik fayllar rejalashtirilgan cleanup orqali o‘chiriladi.

Saved → submitted atomar va idempotent. Submitted/graded yozuvni o‘quvchi o‘chira yoki almashtira olmaydi. Yangi mashq yangi Recording yaratadi. Baholash expected revision orqali bajariladi: eskirgan so‘rov 409; 1–5 butun baho va bo‘sh bo‘lmagan izoh majburiy. Birinchi baholovchi/vaqt saqlanadi; keyingi tahrir alohida API amali.

Hisob o‘chirish: UI’da alohida tasdiq → sessiyalarni bekor qilish → shaxsiy ma’lumotlarni va file cleanup joblarni bir DB tranzaksiyada saqlash/o‘chirish → commitdan keyin fayllarni tozalash. Xatolar retry jobda qoladi. Umumiy materiallar o‘chirilmaydi.

## 8. Interfeys

Sahifalar: kirish/ro‘yxatdan o‘tish/reset, Library, Audio detail + recorder, My Records, admin material/user/group/recording/review boshqaruvi. Soxta hisoblar va statistikalar qo‘yilmaydi; yangi DB uchun haqiqiy bo‘sh holatlar bo‘ladi.

Tasdiqlangan logo asl rasm shaklida saqlanadi; dastlab CSS crop yordamida wordmark/ikonka ko‘rsatilishi mumkin, qayta harf terilmaydi. Alohida shaffof eksport kerak bo‘lsa originaldan shaklni buzmay tayyorlanadi va raster deb belgilanadi.

Vinil Library va audio sahifasida, kasseta My Records’da. Glass navigatsiya, filtr, player, recorder va dialoglarda. Uzun matn/jadval uchun kontrast qatlami. Responsive telefon layout, keyboard fokus, status/aria-live, prefers-reduced-motion va shaffoflikni kamaytirish sozlamasi. Harakat haqiqiy player/record holatiga bog‘lanadi; sun’iy waveform berilmaydi.

## 9. Bosqichlar va qabul mezonlari

- [x] Manbalar, Git, muhit va vizual materiallarni o‘qish.
- [x] Stack variantlari, model, media, sessiya va test rejasini yozish.
- [x] Mavjud mahsulot spetsifikatsiyasi va texnik taklif 2026-11-02 kuni tasdiqlandi.
- [x] **1. Poydevor:** backend/frontend scaffold, environment namuna, custom user, migratsiyalar, auth/reset, bootstrap admin, glass shell. Qabul: haqiqiy register/login/logout; foydalanuvchi admin bo‘la olmaydi; maxfiy sozlamalar Gitga kirmaydi.
- [x] **2. Huquqlar va guruhlar:** effective restrictions, bulk transfer, bloklash va sessiya invalidation. Qabul: API orqali cheklovni aylanib o‘tib bo‘lmaydi; transfer natijalarni saqlaydi.
- [x] **3. Materiallar/media:** upload tekshiruvi, versioning, publish/archive, private range streaming, Library/player/script. Qabul: haqiqiy audio ijrosi va URLga to‘g‘ridan-to‘g‘ri access testlari.
- [x] **4. Tinglash:** interval algoritmi, heartbeat, transaction/idempotency, parallel tablar. Qabul: qisqa ijro/seek/retry hisobni oshirmaydi; to‘liq pauzali tinglash +1 beradi.
- [x] **5. Recorder/My Records:** mikrofon, preview, retry-safe upload, shaxsiy ro‘yxat, tanlab submit/delete. Qabul: haqiqiy brauzerda media oqimi va boshqa userga access rad etilishi.
- [x] **6. Admin:** materiallar, userlar, guruhlar, umumiy yozuvlar va alohida queue, baholash va revision conflict, hisob deletion cleanup. Qabul: 409 holati, majburiy izoh, unblockdan keyin eski session rad etilishi.
- [ ] **7. Reliz tekshiruvi:** PostgreSQL concurrency testlari, frontend build/typecheck, brauzer media/accessibility/responsive, setup/SMTP/storage/backup hujjatlari.

Har bosqichda unga tegishli testlar bilan ishlaydigan natija beriladi. Asosiy MVP barcha bosqichlar bajarilgandagina tayyor hisoblanadi. Hozir tashqi servis, SMTP yoki hosting ulangan emas.

## 10. Muhim testlar

- Auth/permission: student→admin so‘rovi, boshqa user yozuvi, yashirin URL, blocked session, reset token, CSRF.
- Restrictions: personal+group birlashmasi, transfer/unassign, active playbackda cheklov, eski recording saqlanishi.
- Listening: 0.25 s chegarasi va undan katta gap, ko‘p kichik gaplar jami, replay overlap, pause/buffer, sakrashni keyin tinglash, eskirgan sequence, heartbeat timeout, parallel start/finish, duplicate finish, yangi version.
- Recordings: haqiqiy format metadata, hajm limitlari, retry dublikat yaratmasligi, submit race, submitted delete taqiqi.
- Reviews: noto‘g‘ri score, bo‘sh comment, bir vaqtdagi grading, edit audit.
- Cleanup: DB rollback, fayl o‘chirish xatosi va qayta urinish; material fayli saqlanishi.
- Browser: desktop/mobile Chromium, Firefox va WebKit imkon qadar; haqiqiy mikrofon alohida qo‘lda tekshiriladi, sun’iy audio testi haqiqiy qurilma sinovi deb atalmasin.

PostgreSQLga xos tranzaksiya testlari SQLite testlari bilan almashtirilmaydi. CI’da DB xizmati, server testlari va frontend build ishlaydi. Haqiqiy mikrofon yoki brauzer mavjud bo‘lmasa tekshirilmagan holat aniq qayd etiladi.

## 11. Rasmiy manbalar

2026-11-02 kuni tekshirildi:

- Django auth: https://docs.djangoproject.com/en/5.2/topics/auth/default/
- Django storage: https://docs.djangoproject.com/en/5.2/ref/files/storage/
- Vite setup/moslik: https://vite.dev/guide/
- Brauzer yozish API: https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder

## 12. Reja self-review

Manbalar bilan qarama-qarshiliklar tekshirildi: ommaviy count, tezlik boshqaruvi, AI/TTS va auto-submit qo‘shilmagan. Bootstrap admin public emas. Oldingi natijalar versionga, guruhga emas, bog‘langan. Lokal SQLite chegarasi va haqiqiy PostgreSQL tekshiruvi ajratilgan. Yopiq fayllar, session invalidation, optimistic grading va cleanup retry alohida belgilangan. Yangi mahsulot funksiyasi yoki yangi vizual tanlov talab qilinmaydi.

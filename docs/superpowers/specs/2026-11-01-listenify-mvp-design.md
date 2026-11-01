# Listenify — MVP dizayn spetsifikatsiyasi

Sana: 2026-11-01, Asia/Tashkent.

Holat: suhbatda kelishilgan funksiyalar va vizual yo‘nalish jamlangan; yozma spetsifikatsiya yakuniy ko‘rib chiqish uchun tayyor. Mahsulot kodi hali yaratilmagan.

## 1. Maqsad va MVP chegarasi

Listenify ingliz tilida tinglab tushunish va talaffuzni rivojlantirish uchun web-platforma. Mustaqil o‘quvchilar va o‘quv markazi guruhlari bir tizimdan foydalanadi.

Asosiy jarayon: darajaga mos audioni tanlash → tinglash va skriptni o‘qish → audio yoki uning qismini takrorlab ovoz yozish → yozuvni saqlash → ixtiyoriy tekshirishga yuborish → adminning baho va yozma izohini olish.

MVP: hisoblar, audio kutubxona, skriptlar, to‘liq tinglashlar hisobi, audio sahifasida ovoz yozish, My Records, qo‘lda baholash, guruhlar, guruhga ko‘chirish, daraja cheklovlari va admin boshqaruvi.

MVP tashqarisida: alohida talaffuz bo‘limi, erkin matndan ovoz yaratish/TTS, avtomatik yoki AI talaffuz tahlili, listening savol-topshiriqlari, imtihonlar, sertifikatlar, to‘lov va obuna, mobil native ilova. Audio ijro tezligini o‘zgartirish funksiyasi qo‘shilmaydi.

## 2. Hisoblar, rollar va guruhlar

Ikki rol: o‘quvchi va admin. Dars beradigan va yozuvlarni tekshiradigan o‘qituvchilar ham admin rolini oladi. Barcha adminlarning vakolati bir xil: ular barcha o‘quvchilarni, yozuvlarni, guruhlarni va materiallarni boshqaradi; hisobni bloklash va o‘chirish ham shu huquqqa kiradi.

O‘quvchi mustaqil ro‘yxatdan o‘tadi va guruhsiz ham foydalanadi. MVP uchun taklif qilinayotgan hisob usuli: ism, email va parol; kirish email/parol orqali, email orqali parol tiklash. Bu texnik reja uchun ishchi tanlov, suhbatda alohida tanlangan autentifikatsiya provayderi yo‘q. Foydalanuvchi o‘ziga admin rolini bera olmaydi. Birinchi admin xavfsiz boshlang‘ich sozlash orqali tayinlanadi.

Bir o‘quvchi bir vaqtda ko‘pi bilan bitta guruhga a’zo. Admin guruh yaratadi, nomini o‘zgartiradi va mavjud o‘quvchilarni biriktiradi. Guruhga biriktirish o‘quvchining boshqa shaxsiy ma’lumotlarini o‘zgartirmaydi.

Admin bitta yoki bir nechta o‘quvchini boshqa guruhga ko‘chiradi yoki guruhsiz holatga qaytaradi. Tasdiqlashda kimlar qaysi guruhga o‘tayotgani ko‘rsatiladi. Amal yaxlit bajariladi: eski a’zolik tugaydi, yangi a’zolik o‘rnatiladi; tinglashlar, yozuvlar, baho va izohlar saqlanadi. Eski guruh cheklovlari ta’siri tugaydi, yangi guruhniki qo‘llanadi; shaxsiy cheklovlar o‘zgarmaydi.

## 3. Darajalar va kirish qoidalari

Uch daraja bo‘limi: A1–A2, B1–B2, C1–C2. Dastlab barcha darajalar barcha faol o‘quvchilarga ochiq. Admin tanlangan o‘quvchi yoki guruh uchun darajani yopadi va qayta ochadi. Platforma bo‘yicha barcha foydalanuvchilarga umumiy yopish MVP’ga kirmaydi.

Samarali cheklov = shaxsiy yopiq darajalar va joriy guruhning yopiq darajalari birlashmasi. Ulardan bittasida daraja yopiq bo‘lsa, o‘quvchi shu darajaga kira olmaydi. Ochish uchun barcha tegishli cheklovlar olib tashlanishi kerak.

Cheklov audio, skript va ular fayliga to‘g‘ridan-to‘g‘ri kirishda ham serverda tekshiriladi. Cheklangan yoki arxivlangan materialga yangi tinglash yoki yangi yozuv yuborish boshlanmaydi. Oldingi tinglashlar, o‘z yozuvlari va baholar My Records’da saqlanadi. Faol ijro paytida cheklov o‘zgarsa, keyingi server tekshiruvi yangi kirishni rad etadi; avval brauzerga yetib kelgan audio baytlarini qaytarib olish imkoni yo‘q.

## 4. Audio kutubxona va materiallar

Admin materialga sarlavha, daraja, audio fayl va skript kiritadi. Sarlavha, daraja va skript bilan audio yuklanishi yakunlangach e’lon qilish mumkin. Holatlar: qoralama, e’lon qilingan, arxivlangan. O‘quvchi faqat e’lon qilingan va unga ruxsat etilgan materialni ko‘radi.

Kutubxonada daraja filtri, nom bo‘yicha qidiruv va audio kartalari bor. Audio sahifasida play/pauza, vaqt va ijro yo‘li, ovoz balandligi, skriptni ochish/yashirish, shaxsiy to‘liq tinglash soni va ovoz yozish mavjud. Ijro yo‘lida oldinga/orqaga o‘tish mumkin, ammo o‘tkazib yuborilgan qism to‘liq tinglangan hisoblanmaydi.

Materialning audio fayli yoki unga mos skripti mazmunan almashtirilsa yangi versiya yaratiladi. Natijalar va yozuvlar aniq versiyaga bog‘lanadi. Yangi versiya eski to‘liq tinglash sonini meros olmaydi. Oddiy sarlavha yoki tavsif tuzatishi versiyani almashtirmaydi.

Foydalanilgan materialni arxivlash uni kutubxonadan yashiradi, ammo oldingi yozuvlar bilan bog‘lanishini saqlaydi. Admin baholash uchun tegishli eski audio va skriptga kira oladi. O‘quvchi eski ovoz yozuvini tinglaydi; arxivlangan asl audio yangi mashq uchun ochilmaydi.

## 5. To‘liq tinglash hisoblagichi

O‘quvchi faqat o‘z natijasini ko‘radi: “Siz bu audioni N marta to‘liq tinglagansiz”. Admin barcha o‘quvchilarning natijalarini ko‘radi. Ommaviy jami tinglash soni yo‘q.

Har bir urinish audio boshidan boshlanadi. Pauza, davom ettirish va orqaga qaytish mumkin. Oldinga o‘tkazilgan interval keyin odatiy tezlikda tinglanmaguncha to‘liq qamrovga kirmaydi. To‘liq qamrov va audio yakuni bir urinishda tasdiqlangandagina hisob bir marta +1 bo‘ladi.

Server urinish identifikatori, audio versiyasi, ijro holati, eshitilgan vaqt intervallari va o‘tgan haqiqiy vaqtni tekshiradi. Faqat play bosilishi, bitta ended hodisasi yoki foydalanuvchi jo‘natgan tayyor count qiymati yetarli emas. Qayta yuborilgan yakunlash so‘rovi ikkinchi marta hisoblanmaydi; yakunlash va hisob oshishi bitta tranzaksiyada bajariladi.

Media vaqtining yaxlitlash xatolari uchun urinish bo‘yicha jami ko‘pi bilan 0.25 soniyalik qamrov toleransi olinadi. Tekshirilgan odatiy ijro vaqti ham audio davomiyligidan ko‘pi bilan 0.25 soniya kam bo‘lishi mumkin; pauza va buffering vaqti ijro vaqtiga qo‘shilmaydi. Bundan kattaroq sakrab o‘tilgan interval to‘liq tinglash hisoblanmaydi. Bir foydalanuvchi va bir audio versiyasi uchun parallel tablardan hisobni ko‘paytirish oldini olish maqsadida bir vaqtda bitta hisoblanadigan urinish ishlaydi; yangi urinish avvalgisini bekor qiladi.

Sahifa yangilansa/yopilsa tugallanmagan urinish bekor bo‘ladi. Tasdiqlangan natijalar saqlanadi. Tarmoq uzilganda ijro davom etishi mumkin, lekin server tasdiqlamagan urinish hisobga qo‘shilmaydi; foydalanuvchiga holat ko‘rsatiladi. Hisobni oshirish uchun yangi, tekshiriladigan urinish kerak.

Bu tizim ijro va qamrovni tekshiradi; foydalanuvchining diqqat bilan eshitganini isbotlamaydi. Faqat mijoz hodisalari asosida mutlaq firibgarliksizlik va’da qilinmaydi.

## 6. Ovoz yozish va My Records

Ovoz yozish faqat audio sahifasida. O‘quvchi namuna audioni tinglaydi, butun audio yoki bir qismini takrorlaydi. Yozuv audio versiyasi va yozuv egasiga bog‘lanadi. Alohida talaffuz mashqlari va o‘quvchi kiritadigan erkin matn maydoni yo‘q.

Jarayon: mikrofon ruxsati → boshlash → to‘xtatish → tinglab ko‘rish → qayta yozish yoki saqlash. Record boshlanganda asl audio pauzaga o‘tadi. Saqlash faqat fayl serverga muvaffaqiyatli yuklangach tasdiqlanadi. Yuklash xatosida sahifa ochiq ekan qayta urinish mumkin; saqlanmagan yozuvni sahifadan chiqishda yo‘qotish haqida xabar beriladi.

My Records’da yozuv nomi, sana, davomiylik, tegishli audio va holati bor. Faqat o‘zi va adminlar ko‘ra oladi.

| Holat | O‘quvchi amali | Admin amali |
|---|---|---|
| Yuborilmagan | Tinglash, o‘chirish, tekshirishga yuborish | Ko‘rish va tinglash; tekshirish navbatida emas |
| Tekshirishga yuborilgan | Tinglash; yuborilgan nusxani almashtirish/o‘chirish yo‘q | Navbatda tinglash va baholash |
| Baholangan | Tinglash, 1–5 baho va izohni ko‘rish | Bahoni/izohni tahrirlash |

Qayta mashq qilish yangi yozuv yaratadi; avvalgi baho va izoh saqlanadi. Hech bir yozuv avtomatik tekshirishga yuborilmaydi.

## 7. Admin panel va baholash

Bo‘limlar: Audiolar; Foydalanuvchilar; Guruhlar; Ovoz yozuvlari/tekshirish navbati. Ro‘yxatlar o‘quvchi, guruh, audio va holat bo‘yicha filtrlana oladi. Hamma saqlangan yozuvlarni ko‘rish bilan tekshirish navbati alohida tushunchalar.

Admin yuborilgan yozuvni tinglaydi, kerak bo‘lsa asl audio va skript bilan solishtiradi. Baho — 1, 2, 3, 4 yoki 5. Yozma izoh majburiy. Ikkalasi mavjud bo‘lgach “Baholangan” holati o‘rnatiladi. My Records’da baho, izoh, baholagan admin va vaqt ko‘rinadi.

Bir yozuvga bir vaqtda ikki admin baho bersa, ikkinchi eskirgan saqlash rad etiladi; sahifani yangilab joriy holat ko‘rsatiladi. Keyingi tahrir alohida amal sifatida mumkin. Dastlabki baholagan admin/vaqt va oxirgi tahrir admini/vaqti qayd etiladi.

Bloklash foydalanuvchi ma’lumotlarini saqlaydi, hisobga yangi kirishni va faol sessiyalar orqali ishlashni to‘xtatadi. Blokdan chiqarish kirish huquqini tiklaydi; tugatilgan sessiyalar avtomatik qayta ochilmaydi.

Hisob o‘chirish alohida tasdiqlanadi. Uning shaxsiy natijalari, a’zoligi va ovoz fayllari ham o‘chiriladi. Hisob o‘chirish — umumiy audio kutubxonasini o‘chirish degani emas. Fayllarni tozalashdagi xatolar qayta urinish uchun qayd qilinadi; foydalanuvchiga o‘chirilgan hisob bilan kirishga ruxsat berilmaydi.

## 8. Kelishilgan vizual yo‘nalish

Asosiy namuna: Photo Glass v5. Kutubxona uchun foydalanuvchi bergan vinil rasmi, My Records uchun shaffof kassetali yashil rasm ishlatiladi. Audio sahifasi kutubxona mavzusini davom ettiradi. Admin shu palitrada, jadvallar uchun o‘qilishi aniqroq mahalliy fon bilan ishlaydi.

Loyihaga biriktirilgan manbalar:

- [Library foni](visuals/library-background.jpg)
- [My Records foni](visuals/records-background.jpg)
- [Foydalanuvchi yuborgan liquid glass referensi](visuals/glass-material-reference.png)
- [Kelishilgan yo‘nalishdagi interaktiv maket](visuals/listenify-photo-glass-v5.html)

Palitra vinilning quyuq yashil/qora ranglari, kassetaning yorqin yashili, sutrang oq va och mint akslardan iborat. Tipografiya: Manrope sarlavhalar va DM Sans asosiy matn; shrift yuklanmasa tizim sans-serif. Namuna Spotify ruhidan ilhomlangan, mustaqil Listenify logotipi va interfeysi bilan.

Shisha materiali: tiniq markaz, past oq tus, yumaloq yorug‘ chetlar, pastki yashil aks va fonning chetlarda linzaga o‘xshab egilishi. Asosiy joylar: navigatsiya, player, qidiruv, daraja tanlash, yozuv paneli, dialog va toast. Uzun skriptlar, izohlar va jadvallarga mahalliy kontrast qatlami beriladi.

Harakatlar: sudraladigan navigatsiya linzasi; tezlikka mos cho‘zilish va prujinasimon qaytish; tugma bosilishiga tez javob va elastik bo‘shashish; kursor tomon siljiydigan aks; record indikatorining yumshoq kengayishi. Dekorativ harakat o‘quv jarayoniga xalaqit bermaydi. Native iOS rendereri bilan aynan bir xil ko‘rinish va’da qilinmaydi; refraction qo‘llanmasa shaffof/xira fallback qoladi.

Telefon ekranida menyu ixchamlashadi, kartalar ro‘yxatga aylanadi, player va skript ketma-ket turadi. Fon cover orqali moslashtiriladi; suratning muhim markaziy qismi saqlanadi. Klaviatura fokusi, matnli statuslar, kamaytirilgan harakat va shaffoflikni kamaytirish mavjud bo‘ladi.

Maketdagi namunaviy sonlar, statik ajratilgan skript jumlasi, harakatdagi waveform va play/record simulyatsiyasi mahsulotdagi qo‘shimcha imkoniyat va’dasi emas. Yakuniy waveform real ijro/yozuvga bog‘lanadi yoki oddiy ijro ko‘rsatkichi bilan almashtiriladi; vaqtga sinxron transkript MVP talabiga kirmaydi. Maketdagi o‘quvchi va admin tablari faqat dizayn ko‘rish uchun yonma-yon; mahsulotda rol huquqlari qo‘llanadi.

## 9. Arxitektura va ma’lumotlar chegarasi

Bitta web-ilova, mas’uliyati ajratilgan modullar: hisoblar/huquqlar; guruhlar/cheklovlar; materiallar/versiyalar; tinglash urinishlari/natijalar; yozuvlar/yuklash; baholash; admin interfeysi. Aniq framework, hosting va fayl ombori provayderi implementatsiya rejasida tanlanadi; hali xizmat yaratilmagan yoki xarid qilinmagan.

Relyatsion ma’lumotlar bazasida foydalanuvchilar, sessiyalar, guruhlar, a’zolik, shaxsiy/guruh daraja cheklovlari, materiallar, versiyalar, tinglash urinishlari, natijalar, yozuv metadata va baholar saqlanadi. Ovoz va audio fayllar yopiq fayl omborida; kirish server tekshirgan oqim yoki qisqa muddatli ruxsat orqali beriladi. Har bir tekshiruv foydalanuvchi kimligi, holati va tegishli resursga huquqini tekshiradi.

Tinglash qamrovi va hisobning oshishi, guruhga ko‘chirish, tekshirishga yuborish va baholash atomar o‘tishlar bo‘ladi. Qayta so‘rovlar dublikat natija yaratmaydi. DB va fayl ombori orasidagi tozalash qayta urinishga chidamli bo‘ladi.

## 10. Xatolar va tayyorlik mezonlari

Kerakli holatlar: yuklanish, bo‘sh kutubxona/qidiruv/yozuvlar, ruxsat yo‘qligi, yopiq daraja, arxivlangan audio, mikrofon rad etilishi yoki qo‘llanmasligi, ijro xatosi, upload uzilishi/qayta urinish, tarmoq uzilishi, eskirgan baholash, bloklangan hisob. Hech bir xatoda server tasdiqlamagan natija saqlangan deb ko‘rsatilmaydi.

Asosiy tekshirish mezonlari:

1. Qisqa play, oxiriga sakrash, qamrov yetishmasligi va takroriy finish so‘rovlari count oshirmaydi. Pauzali to‘liq tinglash bir marta oshiradi. Versiyalar, tarmoq uzilishi va parallel tab holatlari tekshiriladi.
2. O‘quvchi faqat ruxsatli audioga va o‘z yozuvlariga kira oladi; URL yoki API so‘rovi orqali cheklovni aylanib o‘ta olmaydi. Barcha admin huquqlari serverda tekshiriladi.
3. Guruh ko‘chirish natijalarni saqlaydi, samarali cheklovlarni to‘g‘ri yangilaydi. Guruhsiz foydalanuvchiga shaxsiy cheklovlar qoladi.
4. Ovoz yozish, qayta tinglash, yuklash, qayta urinish va tanlab yuborish haqiqiy brauzerda ishlaydi; o‘quvchi yuborgan nusxani almashtira olmaydi.
5. Majburiy 1–5 baho va izoh My Records’da ko‘rinadi. Parallel baholashda o‘zgarish jim ustiga yozilmaydi.
6. Bloklash sessiyalarni to‘xtatadi; hisob o‘chirish shaxsiy DB ma’lumotlari va fayllar tozalanishini ta’minlaydi.
7. Desktop va telefonlarda navigatsiya, fon joylashuvi, matn kontrasti, klaviatura fokusi, dialoglar va kamaytirilgan harakat tekshiriladi. Browser media formatlari va refraction fallback alohida sinaladi.

Avtomatik tekshiruvlar asosan tinglash algoritmi, kirish huquqlari, holat o‘tishlari va guruh cheklovlariga qaratiladi. Mikrofon, ijro va dizayn haqiqiy brauzerlarda tekshiriladi.

## 11. Ishlab chiqish tartibi

Yozma spetsifikatsiya ko‘rib chiqilgach: texnik stack va muhit rejasi → hisoblar va guruh/huquq poydevori → audio kutubxona va media ombori → tinglash hisoblagichi → ovoz yozish va My Records → baholash va admin oqimlari → photo glass material/motion integratsiyasi → asosiy tekshiruvlar va chiqarishga tayyorlash.

Bu tartib funksiyalarni topshirish bosqichlari; birinchi MVP relizi kelishilgan asosiy imkoniyatlarning barchasini qamrab oladi. Hostingga chiqarish yoki tashqi xizmat ulash ushbu spetsifikatsiya yozilganining o‘zi bilan bajarilgan hisoblanmaydi.

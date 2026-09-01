# AIVORA OBUNA BOT

Telegram bot — Gemini Pro va yopiq kanal obunalarini sotish uchun.

## Xususiyatlar

- ✅ Majburiy kanal obunasi (@aivora_uz)
- ✅ Gemini Pro (35 000 so'm) va Yopiq kanal (100 000 so'm)
- ✅ Admin paneldan yangi obuna qo'shish, narx, tavsif, linklar
- ✅ Har bir link faqat 1 marta 1 foydalanuvchiga beriladi
- ✅ To'lov: karta + chek rasmi → admin tasdiqlaydi → link yuboriladi
- ✅ Miqdor tanlash (1–10)
- ✅ Referal tizimi (10 ta odam → xabar)
- ✅ Izohlar tizimi
- ✅ Kartalar boshqaruvi (qo'shish, o'zgartirish, o'chirish)
- ✅ Statistika (jami daromad, buyurtmalar, foydalanuvchilar)
- ✅ Reklama (broadcast)
- ✅ Sozlamalar (barcha matnlar o'zgartiriladi)
- ✅ Bekor qilish tugmalari
- ✅ Render.com Web Service uchun tayyor (webhook)

## Render.com ga joylash

1. **GitHub** ga yuklang yoki Render Dashboard dan **New → Web Service**
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `python main.py`
4. **Environment Variables** qo'shing:

| Key            | Value                                      |
|----------------|--------------------------------------------|
| BOT_TOKEN      | @BotFather dan olingan token               |
| ADMIN_IDS      | Sizning Telegram ID (vergul bilan ko'p)   |
| WEBHOOK_HOST   | `https://YOUR-APP-NAME.onrender.com`       |
| ADMIN_USERNAME | ABDRFV_11                                  |
| REQUIRED_CHANNEL | @aivora_uz                               |
| PORT           | 10000 (Render avtomatik beradi)            |

5. Deploy qiling.
6. BotFather da hech narsa qilish shart emas — webhook avtomatik o'rnatiladi.

### Telegram ID ni qanday bilish?
@userinfobot yoki @getmyid_bot ga /start yuboring.

### Bot token
@BotFather → /newbot → token ni oling.

## Lokal ishga tushirish (polling)

```bash
cp .env.example .env
# .env ni to'ldiring (WEBHOOK_HOST ni bo'sh qoldiring)
pip install -r requirements.txt
python main.py
```

## Admin panel buyruqlari

- 🛠 Admin Panel — asosiy boshqaruv
- 📊 Statistika
- 💳 Kartalar (qo'shish / o'zgartirish / o'chirish)
- 📦 Obunalar boshqaruvi (yangi obuna, narx, tavsif, yoqish/o'chirish)
- 🔗 Linklar qo'shish
- ⚙️ Sozlamalar (barcha matnlar)
- 📢 Reklama (barcha userlarga xabar)
- 📋 Buyurtmalar
- 👥 Foydalanuvchilar soni

## To'lov jarayoni

1. Foydalanuvchi obunani tanlaydi
2. Miqdorni tanlaydi (1-10)
3. Kartaga to'lov qiladi
4. «To'lov qildim» → chek rasmini yuboradi
5. Bot chekni adminga yuboradi
6. Admin «✅ Tasdiqlash» bosadi
7. Bot foydalanuvchiga noyob link(lar)ni yuboradi
8. Link ishlatilgan deb belgilanadi (qayta berilmaydi)

## Eslatma

- SQLite ishlatiladi (Render free tier da fayl saqlanadi, lekin sleep paytida yo'qolishi mumkin — muhim ma'lumotlar uchun PostgreSQL tavsiya etiladi).
- Free Render 15 daqiqadan keyin uxlaydi — birinchi so'rov sekin bo'lishi mumkin.
- Production uchun PostgreSQL + persistent disk tavsiya etiladi.

## Muallif

AIVORA — @aivora_uz
Admin: @ABDRFV_11

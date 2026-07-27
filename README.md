# Ultra Gaming VPN — Railway Deploy

## ساختار فایل‌ها

```
ultra-gaming-vpn/
├── Dockerfile
├── config.json          ← Xray (5 inbound)
├── nginx.conf.tmpl      ← nginx template (PORT env)
├── start.sh             ← boot sequence
├── stats_api.py         ← live stats HTTP server
├── dashboard/
│   └── index.html       ← management panel
└── cloudflare-worker.js ← CF Worker (جداگانه deploy کن)
```

## Deploy روی Railway

1. یه GitHub repo جدید بساز
2. همه این فایل‌ها رو push کن
3. Railway → New Project → Deploy from GitHub
4. Railway خودکار Dockerfile رو detect می‌کنه
5. بذار build بشه، done.

## پنل مدیریت

```
https://[RAILWAY-DOMAIN]/dashboard/
```

CPU · RAM · Network Speed (live graph) · Uptime · همه کانفیگ‌ها

---

## کانفیگ‌ها

> جایگزین کن: `YOUR-RAILWAY-DOMAIN` = دامنه Railway ات

### ⚡ BEST — VLESS + HTTPUpgrade (کمترین لیتنسی، خوراک گیم)
```
vless://b684dabf-bc91-46bd-bb7e-477bfdc5ca01@YOUR-RAILWAY-DOMAIN:443?encryption=none&security=tls&sni=YOUR-RAILWAY-DOMAIN&type=httpupgrade&path=%2Fupgrade&host=YOUR-RAILWAY-DOMAIN#Gaming-Ultra-Direct
```

### VLESS + WebSocket (direct)
```
vless://b684dabf-bc91-46bd-bb7e-477bfdc5ca01@YOUR-RAILWAY-DOMAIN:443?encryption=none&security=tls&sni=YOUR-RAILWAY-DOMAIN&type=ws&path=%2Fvless&host=YOUR-RAILWAY-DOMAIN#Gaming-VLESS-WS
```

### VMess + WebSocket
```
vmess://[base64 از پنل بگیر]
```

### Trojan + WebSocket (pass: gaming2025ultra)
```
trojan://gaming2025ultra@YOUR-RAILWAY-DOMAIN:443?security=tls&sni=YOUR-RAILWAY-DOMAIN&type=ws&path=%2Ftrojan&host=YOUR-RAILWAY-DOMAIN#Gaming-Trojan-WS
```

### VLESS + SplitHTTP
```
vless://b684dabf-bc91-46bd-bb7e-477bfdc5ca01@YOUR-RAILWAY-DOMAIN:443?encryption=none&security=tls&sni=YOUR-RAILWAY-DOMAIN&type=splithttp&path=%2Fsplit&host=YOUR-RAILWAY-DOMAIN#Gaming-SplitHTTP
```

---

## Cloudflare Worker

1. workers.cloudflare.com → Create Worker
2. محتوای `cloudflare-worker.js` رو paste کن
3. Deploy
4. Settings → Triggers → Cron → هر 1 دقیقه: `* * * * *`
5. Settings → Placement → Smart

کانفیگ‌های CF Worker (جایگزین `YOUR-CF-DOMAIN`):

```
# CF + HTTPUpgrade (بهترین)
vless://b684dabf-bc91-46bd-bb7e-477bfdc5ca01@YOUR-CF-DOMAIN:443?encryption=none&security=tls&sni=YOUR-CF-DOMAIN&type=httpupgrade&path=%2Fupgrade&host=YOUR-CF-DOMAIN#Gaming-CF-Ultra

# CF + WS
vless://b684dabf-bc91-46bd-bb7e-477bfdc5ca01@YOUR-CF-DOMAIN:443?encryption=none&security=tls&sni=YOUR-CF-DOMAIN&type=ws&path=%2Fvless&host=YOUR-CF-DOMAIN#Gaming-CF-WS
```

---

## تنظیمات Hiddify (گیمینگ)

| Setting | Value |
|---------|-------|
| Mux | OFF |
| Fragment | tlshello, 50-100, 3-5 |
| Bypass LAN | ON |
| DNS | 8.8.8.8 |

---

## Architecture

```
Internet
   │ TLS 443
   ▼
Railway (nginx :8080)
   ├── /vless    → Xray :7001 (VLESS WS)
   ├── /vmess    → Xray :7002 (VMess WS)
   ├── /trojan   → Xray :7003 (Trojan WS)
   ├── /upgrade  → Xray :7004 (VLESS HTTPUpgrade) ⚡
   ├── /split    → Xray :7005 (VLESS SplitHTTP)
   ├── /api/     → Stats API :8888
   └── /dashboard/ → Management Panel (HTML)
```

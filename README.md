# Fatima Youth Federation of Yayamulla

Social media platform for the FYFY community — share photos, videos, audio, events, and connect with fellow members.

## 🚀 Run Locally

### 1. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 2. Copy environment file
```bash
copy .env.example .env
```
Edit `.env` and set a strong `SECRET_KEY`.

### 3. Run the app
```bash
python app.py
```

Visit: **http://localhost:5000**

### Default Admin Account
- **Email:** `sachin@123`
- **Password:** `@1234sachin`

---

## ☁️ Deploy to Render (Free)

1. Push this folder to a **GitHub repository**
2. Go to [render.com](https://render.com) → New → **Web Service**
3. Connect your GitHub repo
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Environment Variables:** Add `SECRET_KEY` with a random value
5. Click **Deploy** — Render gives you a free public URL!

> **Note:** Render's free tier spins down after 15 min of inactivity. Upgrade for always-on hosting.

---

## ☁️ Deploy to PythonAnywhere (Free)

1. Go to [pythonanywhere.com](https://www.pythonanywhere.com) → Sign up free
2. Upload project files via the **Files** tab (or use git clone)
3. Create a **virtualenv** and install requirements:
   ```bash
   mkvirtualenv fyfy --python=python3.10
   pip install -r requirements.txt
   ```
4. Go to **Web** tab → Add new web app → Flask → point to `app.py`
5. Set `WSGI_FILE` source code directory to your project folder
6. Add environment variable `SECRET_KEY` in the **Web** tab
7. Reload the app — your site is live!

---

## 📁 Project Structure

```
yayamulla/
├── app.py              ← Flask app, all routes & models
├── requirements.txt    ← Python dependencies
├── Procfile            ← For Render/Heroku
├── .env.example        ← Copy to .env and configure
├── static/
│   ├── css/style.css   ← Full design system
│   ├── js/main.js      ← All frontend JS
│   └── uploads/        ← User uploaded media (auto-created)
└── templates/
    ├── base.html       ← Shared layout, navbar
    ├── login.html      ← Sign in page
    ├── signup.html     ← Register page
    ├── feed.html       ← Social feed
    ├── profile.html    ← User profile
    ← events.html       ← Events with Google Maps
    ├── admin.html      ← Admin panel
    └── error.html      ← 403 / 404 pages
```

## ✅ Features

- 🔐 Signup / Login / Logout with secure password hashing
- 📸 Upload photos (JPG, PNG, GIF), videos (MP4), audio (MP3)
- 🔗 Share links
- ❤️ Real-time like/unlike (AJAX)
- 💬 Comment system (AJAX, no page reload)
- 📅 Events page with Google Maps embed
- ⚙️ Admin panel: manage users, delete posts, toggle admin
- 👤 Profile pages with bio and avatar
- 📱 Fully responsive mobile design
- 🌙 Dark glassmorphism UI

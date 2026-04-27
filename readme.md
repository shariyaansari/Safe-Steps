# 🛡️ Safe Steps

**A real-time community crime mapping platform for Mumbai** — empowering residents to report incidents, visualize crime patterns geospatially, and stay ahead of danger through ML-based predictions.

---

## 📌 Overview

Safe Steps is a civic safety platform where users report crime incidents that appear live on a map. Admins verify and moderate reports, while a machine learning layer predicts high-risk zones based on historical and scraped data. Built with parents, commuters, and local communities in mind — particularly for high-density urban areas like Kurla, BKC, and surrounding Mumbai wards.

---

## ✨ Features

### 🔐 Authentication & Roles
- Role-based access: **Admin** and **Parent/Resident**
- Secure login and registration via Flask-Login
- Auto-creates an admin account on first run if none exists
- OTP / 2FA support *(in progress)*

### 📍 Incident Reporting Engine
- Submit reports with: incident type, description, date/time, specific area, and GPS coordinates
- Photo/media upload support *(roadmap)*
- Anonymous reporting layer *(roadmap)*
- Duplicate detection via proximity + time window *(roadmap)*

### 🗺️ Real-Time Map
- Leaflet.js integration for interactive incident visualization
- Live heatmap overlay showing crime density by area
- WebSocket-powered map updates — new reports appear instantly for all connected users *(in progress)*
- Safe route planner avoiding verified hotspot zones *(roadmap)*

### 🛠️ Admin Dashboard
- View, verify, and reject submitted reports
- Incident status workflow: `reported → verified → rejected`
- Community voting: auto-elevate to `community_verified` after threshold upvotes *(roadmap)*
- Full audit log of admin actions *(roadmap)*

### 📊 Analytics
- Month-over-month crime trend charts
- Crime type distribution (theft, assault, harassment, etc.)
- Area-wise incident density for Kurla, BKC, and custom zones
- Safety score per area using recency-weighted formula *(roadmap)*
- Export reports as PDF *(roadmap)*

### 🤖 ML & Predictions
- Historical crime data scraping from Mumbai news sources (RSS feeds)
- Crime hotspot clustering per grid cell
- Random Forest predictor: probability of crime by area, hour, and day *(roadmap)*
- Prediction overlay rendered as a semi-transparent risk map *(roadmap)*

### 🚨 Safety Features *(roadmap)*
- **SOS / Panic Button** — one-tap emergency broadcast to nearby users and admins with live location
- **Area subscriptions** — get push notifications when a verified incident is reported in your ward
- **Public API** — open data endpoints for NGOs and civic apps

---

## 🧱 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, Flask-Login, SQLAlchemy |
| Database | SQLite (dev) → PostgreSQL + PostGIS (prod) |
| Real-time | Flask-SocketIO + Redis pub/sub *(in progress)* |
| Frontend | Jinja2 templates, Leaflet.js, Plotly, custom CSS |
| ML / Data | scikit-learn, pandas, feedparser, BeautifulSoup |
| Background jobs | Celery + Redis *(roadmap)* |
| Auth upgrades | JWT, flask-limiter *(roadmap)* |

---

## 🗂️ Project Structure

```
safe-steps/
├── app.py                    # Flask app factory, blueprints registration
├── models.py                 # SQLAlchemy models: Users, Incident
├── database.py               # DB instance
├── utils.py                  # Analytics queries, heatmap generation
├── update_news_analysis.py   # Seeds local JSON with simulated incident data
├── config.py                 # App configuration
├── blueprints/
│   ├── auth/                 # Login, register, logout
│   ├── admin/                # Admin dashboard, moderation
│   ├── home/                 # Main map view
│   ├── parent/               # User-facing report submission
│   └── news_analysis/        # News & crime analysis feeds
├── templates/                # Jinja2 HTML templates
├── static/                   # CSS, JS, assets
└── requirements.txt
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip
- (Optional) PostgreSQL for production setup

### Installation

```bash
# Clone the repository
git clone https://github.com/shariyaansari/Safe-Steps.git
cd Safe-Steps

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file in the root directory:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///reports.db        # or postgresql://user:pass@localhost/safesteps
FLASK_ENV=development
ADMIN_EMAIL=admin@safesteps.com
ADMIN_PASSWORD=changeme
```

### Run the App

```bash
python app.py
```

Visit `http://localhost:5000` — an admin account is auto-created on first run if one doesn't exist.

---

## 🗺️ Roadmap

### Phase 1 — Complete core (current sprint)
- [x] Incident submission with lat/lng
- [x] Role-based auth (Admin / Parent)
- [x] Heatmap + trend analytics
- [ ] WebSocket real-time map updates
- [ ] Admin verify / reject UI (wire up `status` field)
- [ ] Community upvote / downvote system
- [ ] PostgreSQL + PostGIS migration

### Phase 2 — Safety features
- [ ] Photo upload on incident reports
- [ ] SOS / panic button with live location broadcast
- [ ] Area subscription alerts (Firebase FCM)
- [ ] Safety score per area (recency-weighted formula)
- [ ] Duplicate detection (proximity + time)

### Phase 3 — ML & intelligence
- [ ] Real Mumbai news RSS scraper (replace mocked JSON)
- [ ] Crime hotspot clustering (k-means on PostGIS geometry)
- [ ] Random Forest crime predictor (time + location features)
- [ ] Risk overlay on map

### Phase 4 — Open platform
- [ ] Public REST API for civic apps and NGOs
- [ ] Safe route planner (Leaflet Routing Machine + hotspot avoidance)
- [ ] Mobile-responsive PWA
- [ ] Data export (PDF / CSV reports)

---

## 📐 Database Schema

```
Users
  id, username, email, password (hashed), role, created_at

Incident
  id, user_id (FK), incident_type, description,
  location, area, latitude, longitude,
  incident_date, reported_at, status
```

Planned additions: `IncidentMedia`, `IncidentVote`, `AreaSubscription`, `AuditLog`

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change.

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Commit your changes
git commit -m "feat: add your feature description"

# Push and open a PR
git push origin feature/your-feature-name
```

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [Leaflet.js](https://leafletjs.com/) — open-source maps
- [Plotly](https://plotly.com/) — analytics charts
- [Flask](https://flask.palletsprojects.com/) — web framework
- Inspired by real civic safety needs in Mumbai's high-density neighbourhoods
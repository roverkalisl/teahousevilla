# Teahouse Villa — Website

Django-based villa website: public marketing site + Django Admin for the owner to manage
content. This is Phase 1 (project setup) + Phase 2 (public website) of the full project
spec — booking engine, OTA sync, and deployment come in later phases.

## Stack

- Python 3.13, Django 6.1
- SQLite (dev) — PostgreSQL planned for production
- Bootstrap 5 + Bootstrap Icons (CDN)
- Pillow (image resizing), WhiteNoise (static files), django-environ (env config)

## Local setup

```bash
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; use venv\Scripts\activate.bat on cmd
pip install -r requirements.txt

cp .env.example .env           # then edit SECRET_KEY etc.

python manage.py migrate
python manage.py seed_demo     # loads placeholder villa/room/gallery content
python manage.py createsuperuser

python manage.py runserver
```

Visit http://127.0.0.1:8000/ for the site and http://127.0.0.1:8000/admin/ for the admin panel.

## Project layout

- `config/` — Django project settings/urls
- `property/` — villa content: models (Property, Room, Facility, Media, Price), admin, public views
- `bookings/` — placeholder "coming soon" page for Check Availability / Book Now (real booking
  engine is a later phase)
- `templates/`, `static/` — shared base template, CSS, JS
- `property/management/commands/seed_demo.py` — populates placeholder content for local dev

## What's implemented

- Property/Room/Facility/Media/Price models, fully manageable from Django Admin
- Public pages: Home, About, Rooms (list + detail), Gallery (photos + video embeds), Contact
- WhatsApp click-to-chat, Google Maps embed, social links — all sourced from the Property record
- Responsive, mobile-first layout (Bootstrap 5)

## What's intentionally deferred (later phases per the project spec)

- Availability calendar & direct booking inquiry form (Phase 4)
- Email/WhatsApp automated notifications (Phase 5)
- Airbnb / Booking.com calendar sync (Phase 6)
- Production deployment, PostgreSQL, Cloudinary media storage, SSL, backups (Phase 8)
- sitemap.xml / robots.txt (basic per-page meta title/description is already in place)

The "Check Availability" and "Book Now" buttons currently link to `/booking/`, a placeholder
page pointing guests to WhatsApp/phone/email until the booking engine is built.

# Teahouse Villa — Website

Django-based villa website: a premium, storytelling-style public site (benchmarked against
lushecoscape.com) + Django Admin for the owner to manage content. Booking engine here is a
direct **inquiry** flow (WhatsApp + email capture) — full Airbnb/Booking.com iCal sync and
billing/folio are a later phase.

## Stack

- Python 3.13, Django 6.1
- SQLite (dev) — PostgreSQL planned for production
- Tailwind CSS v4 (compiled via `@tailwindcss/cli`, no Node runtime needed in production) + Bootstrap Icons (CDN)
- Pillow (image resizing), WhiteNoise (static files), django-environ (env config)

## Local setup

```bash
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; use venv\Scripts\activate.bat on cmd
pip install -r requirements.txt

npm install                    # Tailwind CLI (dev dependency only)
npm run build-css              # compiles static/css/tailwind.css

cp .env.example .env           # then edit SECRET_KEY etc.

python manage.py migrate
python manage.py seed_demo     # loads placeholder villa/room/gallery/attractions/testimonials
python manage.py createsuperuser

python manage.py runserver
```

Visit http://127.0.0.1:8000/ for the site and http://127.0.0.1:8000/admin/ for the admin panel.

The custom owner dashboard is available at http://127.0.0.1:8000/admin-login/.
Sign in with an active Django staff user. OTA status is shown under Dashboard > Settings.

## OTA availability status configuration

The dashboard stores one `OTAAvailabilitySyncStatus` row per villa and source
(`Airbnb` and `Booking.com`) with `last_synced_at`, `status`, `last_error`, and
`updated_at`. Open `/admin-dashboard/settings/` and use **Sync now** to run the
configured adapter, or run the scheduled command manually:

```bash
python manage.py sync_ota_availability
```

Set this Render environment variable to enable the adapter:

```text
OTA_SYNC_ENABLED=True
```

When it is `False`, a sync attempt is recorded as failed with a configuration
message. The current adapter records sync health and provides the architecture
for provider integration; it does not yet import Airbnb or Booking.com iCal
events. Do not enable it as a claim of live OTA synchronization until official
iCal/API credentials and import logic are configured.

If you edit `templates/**/*.html` or `static_src/css/input.css`, rerun `npm run build-css`
(or `npm run watch-css` while developing) to regenerate `static/css/tailwind.css` — that
compiled file is committed so the site works without Node on a plain clone/deploy.

## Project layout

- `config/` — Django project settings/urls
- `property/` — villa content: models (Property, Room, Facility, Media, Price, Attraction,
  Testimonial), admin, public views
- `bookings/` — direct Booking Inquiry flow: form (`bookings/forms.py`), view (`bookings/views.py`)
  saves the inquiry, emails the owner, and hands off to a prefilled WhatsApp message
- `templates/`, `static/`, `static_src/` — base template, compiled Tailwind CSS, JS, Tailwind source
- `property/management/commands/seed_demo.py` — populates placeholder content for local dev

## What's implemented

- Property/Room/Facility/Media/Price/Attraction/Testimonial models, fully manageable from Django Admin
- Public pages: Home (story, facilities, rooms, gallery, nearby attractions, testimonials, map),
  About, Rooms (list + detail), Gallery (categorized photos + video embeds), Contact
- Ambient hero: auto-sliding villa photos by default, or an embedded YouTube/Vimeo video if
  `Property.hero_video_url` is set
- Booking Inquiry flow (`/booking/`): date + guest-count form → saves to DB, emails the owner
  (console backend in dev; set `EMAIL_BACKEND`/`EMAIL_HOST*` env vars for real SMTP), and hands
  off to a prefilled `wa.me` WhatsApp link
- WhatsApp click-to-chat, Google Maps embed, social links — all sourced from the Property record
- Responsive, mobile-first layout (Tailwind CSS)

## What's intentionally deferred (later phases per the project spec)

- Full Booking/Folio billing system (F&B & service tabs, payment status)
- Airbnb / Booking.com two-way iCal calendar sync
- WhatsApp Business API automation
- Booking status workflow (pending/confirmed/checked-in/etc.)
- Dynamic seasonal-pricing admin UX beyond the existing `Price` model
- Production deployment, PostgreSQL, Cloudinary media storage, SSL, backups
- sitemap.xml / robots.txt (basic per-page meta title/description is already in place)

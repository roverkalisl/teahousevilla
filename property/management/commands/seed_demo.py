import datetime
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from property.models import Facility, Media, Price, Property, Room

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PLACEHOLDER_DIR = BASE_DIR / "static" / "img" / "placeholders"

FACILITIES = [
    ("Private Pool", "bi-water"),
    ("Free Wi-Fi", "bi-wifi"),
    ("Air Conditioning", "bi-snow"),
    ("Fully Equipped Kitchen", "bi-cup-hot"),
    ("Free Parking", "bi-p-square"),
    ("Garden", "bi-tree"),
    ("BBQ Area", "bi-fire"),
    ("Hot Water", "bi-droplet-half"),
    ("Washing Machine", "bi-basket"),
    ("Breakfast Included", "bi-egg-fried"),
]

ROOMS = [
    {
        "name": "Master Bedroom",
        "description": "A spacious king-bed suite with garden views, an attached bathroom and a private reading nook.",
        "capacity": 2,
        "bed_type": "King Bed",
        "bathroom_info": "Attached Bathroom",
        "image": "bedroom-master.jpg",
    },
    {
        "name": "Garden Room",
        "description": "A cosy queen-bed room opening onto the garden, perfect for a peaceful night's sleep.",
        "capacity": 2,
        "bed_type": "Queen Bed",
        "bathroom_info": "Attached Bathroom",
        "image": "bedroom-garden.jpg",
    },
    {
        "name": "Deluxe Twin Room",
        "description": "Twin beds with plenty of natural light, ideal for friends or siblings travelling together.",
        "capacity": 2,
        "bed_type": "Twin Beds",
        "bathroom_info": "Shared Bathroom",
        "image": "bedroom-deluxe.jpg",
    },
]

GALLERY = [
    ("villa-exterior.jpg", "Villa Exterior", "exterior", True),
    ("villa-pool.jpg", "Private Swimming Pool", "pool", False),
    ("villa-garden.jpg", "Tropical Garden", "garden", False),
    ("villa-kitchen.jpg", "Fully Equipped Kitchen", "kitchen", False),
    ("bathroom-1.jpg", "Modern Bathroom", "bathrooms", False),
    ("nearby-beach.jpg", "Beach Nearby", "nearby", False),
]


class Command(BaseCommand):
    help = "Seeds the database with placeholder villa content for local development."

    def handle(self, *args, **options):
        site, created = Property.objects.get_or_create(
            defaults=dict(
                name="Teahouse Villa",
                tagline="Your Private Retreat by the Hills",
                short_description=(
                    "A serene private villa offering breathtaking views, a private pool and "
                    "warm hospitality — the perfect base for your next getaway."
                ),
                full_description=(
                    "Teahouse Villa is a beautifully appointed private residence set among lush "
                    "gardens. With spacious bedrooms, a private swimming pool and a fully equipped "
                    "kitchen, it offers everything you need for a relaxing family holiday or a "
                    "romantic escape. Our team is on hand to make your stay unforgettable."
                ),
                address="123 Hillside Road, Kandy, Sri Lanka",
                google_maps_url="https://maps.google.com/?q=Kandy+Sri+Lanka",
                google_maps_embed_url="https://maps.google.com/maps?q=Kandy%20Sri%20Lanka&output=embed",
                max_guests=6,
                bedrooms=3,
                bathrooms=3,
                property_size_sqm=350,
                check_in_time=datetime.time(14, 0),
                check_out_time=datetime.time(11, 0),
                house_rules="No smoking indoors.\nNo parties or events.\nPets allowed on request.\nQuiet hours after 10 PM.",
                cancellation_policy="Free cancellation up to 7 days before check-in. 50% refund up to 3 days before check-in.",
                phone_number="+94771234567",
                whatsapp_number="94771234567",
                email="stay@teahousevilla.example",
                facebook_url="https://facebook.com/",
                instagram_url="https://instagram.com/",
                youtube_url="",
                starting_price_override=150,
            )
        )
        if created:
            hero_path = BASE_DIR / "static" / "img" / "hero-placeholder.jpg"
            with hero_path.open("rb") as f:
                site.hero_image.save("hero-placeholder.jpg", File(f), save=True)
            self.stdout.write(self.style.SUCCESS("Created Property: Teahouse Villa"))
        else:
            self.stdout.write("Property already exists, skipping.")

        for name, icon in FACILITIES:
            Facility.objects.get_or_create(name=name, defaults={"icon": icon})
        self.stdout.write(self.style.SUCCESS(f"Ensured {len(FACILITIES)} facilities."))

        all_facilities = list(Facility.objects.all())

        if not Room.objects.exists():
            for order, room_data in enumerate(ROOMS):
                room = Room.objects.create(
                    villa=site,
                    name=room_data["name"],
                    description=room_data["description"],
                    capacity=room_data["capacity"],
                    bed_type=room_data["bed_type"],
                    bathroom_info=room_data["bathroom_info"],
                    has_ac=True,
                    display_order=order,
                )
                room.facilities.set(all_facilities[:5])
                image_path = PLACEHOLDER_DIR / room_data["image"]
                with image_path.open("rb") as f:
                    Media.objects.create(
                        villa=site,
                        room=room,
                        media_type=Media.IMAGE,
                        image=File(f, name=room_data["image"]),
                        caption=room.name,
                        category="bedrooms",
                        is_cover=True,
                        display_order=0,
                    )
            self.stdout.write(self.style.SUCCESS(f"Created {len(ROOMS)} rooms with cover photos."))
        else:
            self.stdout.write("Rooms already exist, skipping.")

        if not Media.objects.filter(room__isnull=True).exists():
            for order, (filename, caption, category, is_cover) in enumerate(GALLERY):
                image_path = PLACEHOLDER_DIR / filename
                with image_path.open("rb") as f:
                    Media.objects.create(
                        villa=site,
                        media_type=Media.IMAGE,
                        image=File(f, name=filename),
                        caption=caption,
                        category=category,
                        is_cover=is_cover,
                        display_order=order,
                    )
            self.stdout.write(self.style.SUCCESS(f"Created {len(GALLERY)} gallery photos."))
        else:
            self.stdout.write("Gallery media already exists, skipping.")

        if not Price.objects.exists():
            Price.objects.create(villa=site, price_type=Price.STANDARD, amount=150, notes="Standard nightly rate")
            Price.objects.create(villa=site, price_type=Price.WEEKEND, amount=190, notes="Friday & Saturday nights")
            Price.objects.create(villa=site, price_type=Price.PEAK, amount=250, notes="December - January")
            self.stdout.write(self.style.SUCCESS("Created sample pricing."))
        else:
            self.stdout.write("Prices already exist, skipping.")

        self.stdout.write(self.style.SUCCESS("Demo data seed complete."))

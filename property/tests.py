from types import SimpleNamespace
from xml.etree import ElementTree

from django.contrib.admin.sites import AdminSite
from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse

from .admin import RoomAdmin
from .models import Media, Property, Room


class SeoEndpointTests(TestCase):
    def setUp(self):
        self.property = Property.objects.create(
            name="Test Villa",
            short_description="A test villa in Galle.",
        )
        self.room = Room.objects.create(
            villa=self.property,
            name="Garden Room",
            active=True,
        )
        self.inactive_room = Room.objects.create(
            villa=self.property,
            name="Archived Room",
            active=False,
        )

    def test_robots_txt_is_plain_text_and_allows_public_assets(self):
        response = self.client.get(reverse("robots_txt"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertIn(b"Allow: /", response.content)
        self.assertIn(b"Disallow: /admin-dashboard/", response.content)
        self.assertIn(
            b"Sitemap: https://teahousevillagalle.com/sitemap.xml",
            response.content,
        )
        self.assertNotIn(b"Disallow: /static/", response.content)
        self.assertNotIn(b"Disallow: /media/", response.content)

    def test_sitemap_is_valid_xml_with_only_public_pages_and_active_rooms(self):
        response = self.client.get(reverse("sitemap"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/xml"))
        sitemap_xml = ElementTree.fromstring(response.content)
        locations = {
            element.text
            for element in sitemap_xml.iter()
            if element.tag.endswith("loc")
        }

        expected_locations = {
            "https://teahousevillagalle.com/",
            "https://teahousevillagalle.com/about/",
            "https://teahousevillagalle.com/property/",
            "https://teahousevillagalle.com/rooms/",
            "https://teahousevillagalle.com/gallery/",
            "https://teahousevillagalle.com/contact/",
            f"https://teahousevillagalle.com{self.room.get_absolute_url()}",
        }
        self.assertEqual(locations, expected_locations)
        self.assertNotIn(
            f"https://teahousevillagalle.com{self.inactive_room.get_absolute_url()}",
            locations,
        )

    def test_public_pages_booking_and_admin_routes_remain_available(self):
        for url in (
            reverse("property:home"),
            reverse("property:about"),
            reverse("property:property_detail"),
            reverse("property:room_list"),
            reverse("property:room_detail", args=[self.room.slug]),
            reverse("property:gallery"),
            reverse("property:contact"),
            reverse("bookings_public:inquire"),
            reverse("bookings:admin_login"),
        ):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

        self.assertEqual(self.client.get(reverse("bookings:dashboard")).status_code, 302)
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_homepage_has_canonical_and_open_graph_metadata(self):
        response = self.client.get(reverse("property:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<link rel="canonical" href="https://teahousevillagalle.com/">',
        )
        self.assertContains(
            response,
            '<meta property="og:url" content="https://teahousevillagalle.com/">',
        )
        self.assertContains(response, "A test villa in Galle.")


class RoomAdminMediaInlineTest(TestCase):
    def test_save_formset_sets_media_villa_from_room(self):
        villa = Property.objects.create(name="Test Villa")
        room = Room.objects.create(villa=villa, name="Deluxe Room", capacity=2)
        admin = RoomAdmin(Room, AdminSite())

        media = Media(room=room, caption="Garden view")

        class DummyFormSet:
            model = Media

            def save(self, commit=False):
                return [media]

            def save_m2m(self):
                pass

        admin.save_formset(None, SimpleNamespace(instance=room), DummyFormSet(), change=False)

        self.assertEqual(media.villa_id, villa.id)
        self.assertEqual(media.room_id, room.id)


class GoogleMapsEmbedUrlValidationTest(TestCase):
    def test_google_maps_embed_url_accepts_iframe_src(self):
        villa = Property(
            name="Test Villa",
            google_maps_embed_url='<iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3967.6267891353573!2d80.31511347498893!3d6.045833843939883!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3ae16d1918493309%3A0xc380c97024f7a283!2sTea%20House%20Villa!5e0!3m2!1sen!2slk!4v1787995710053!5m2!1sen!2slk" width="600" height="450" style="border:0;" allowfullscreen="" loading="lazy" referrerpolicy="strict-origin-when-cross-origin"></iframe>',
        )

        villa.full_clean()

        self.assertEqual(
            villa.google_maps_embed_url,
            "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3967.6267891353573!2d80.31511347498893!3d6.045833843939883!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3ae16d1918493309%3A0xc380c97024f7a283!2sTea%20House%20Villa!5e0!3m2!1sen!2slk!4v1787995710053!5m2!1sen!2slk",
        )


class InvalidMediaImageUploadTest(TestCase):
    def test_invalid_image_upload_does_not_crash_property_edit(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        villa = Property.objects.create(name="Test Villa")

        media = Media(
            villa=villa,
            media_type=Media.IMAGE,
            caption="Broken file",
            image=SimpleUploadedFile("broken.jpg", b"not-a-real-image", content_type="image/jpeg"),
        )

        media.save()

        self.assertFalse(media.image)

    def test_stale_legacy_path_is_cleared_without_cloudinary_upload(self):
        villa = Property.objects.create(name="Test Villa")
        media = Media(villa=villa, media_type=Media.IMAGE, caption="Legacy stale image", image="gallery/does-not-exist.jpg")

        media.save()

        self.assertFalse(media.image)


class MarkdownRenderTest(TestCase):
    def test_markdown_filter_renders_html_and_sanitizes(self):
        template = Template("{% load markdown_filters %}{{ value|markdownify }}")
        rendered = template.render(Context({"value": "# Tea House Villa\n\n**Warm welcome**\n\n- Pool\n- Garden\n\n😊"}))

        self.assertIn("<h1>", rendered)
        self.assertIn("<strong>Warm welcome</strong>", rendered)
        self.assertIn("<ul>", rendered)
        self.assertIn("<li>Pool</li>", rendered)
        self.assertIn("😊", rendered)
        self.assertNotIn("# Tea House Villa", rendered)
        self.assertNotIn("**Warm welcome**", rendered)
        self.assertNotIn("<script>", rendered.lower())

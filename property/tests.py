from types import SimpleNamespace

from django.contrib.admin.sites import AdminSite
from django.template import Context, Template
from django.test import TestCase

from .admin import RoomAdmin
from .models import Media, Property, Room


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

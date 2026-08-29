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

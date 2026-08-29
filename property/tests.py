from types import SimpleNamespace

from django.contrib.admin.sites import AdminSite
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

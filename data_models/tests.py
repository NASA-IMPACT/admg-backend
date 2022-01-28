from django.test import TestCase

from . import serializers


class TestImageSerializers(TestCase):
    def test_draft(self):
        serializer = serializers.ImageSerializer(
            data={
                "description": "Let's see if this will publish",
                "image": "1438940e-94b7-440d-9658-ba9e9a85c0ef.jpeg",
                "owner": "",
                "source_url": "",
                "title": "Test Image",
            }
        )
        serializer.is_valid(raise_exception=True)

import os
import json

from django.core.management.base import BaseCommand, CommandError, CommandParser
from rooms.models import Emoji

from DjangoChatApp.settings import STATICFILES_DIRS
from utils import base64_file

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('support', choices=["apple", "google", "facebook", "windows", "twitter", "joypixels", "samsung", "gmail", "softbank", "docomo", "kddi"], type=str)

    def handle(self, *args, **options):
        # will delete all previous emojis rather than override
        Emoji.objects.all().delete()

        emoji_support = options['support']
        emoji_list_file = os.path.join(STATICFILES_DIRS[0], 'emoji.json')
        with open(emoji_list_file, 'r', encoding='utf-8') as file:
            emojis = filter(lambda emoji: emoji['support'].get(emoji_support), json.loads(file.read())['emojis'])

        for emoji in emojis:
            Emoji.objects.create(
                name=emoji["name"], 
                category=emoji["category"],
                image=base64_file(emoji["images"][emoji_support]),   
                emoji_literal=emoji["emoji"],
            )
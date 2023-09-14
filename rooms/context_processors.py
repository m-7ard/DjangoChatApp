import os
import json

from DjangoChatApp.settings import STATICFILES_DIRS

# def room_list(request):
# 	context = {
# 		'room_list': Room.objects.all()
# 	}
# 	return context

def emoji_iteratable(request):
    def get_iteratable():
        emoji_file = os.path.join(STATICFILES_DIRS[0], 'emoji.json')
        with open(emoji_file, 'r', encoding='utf-8') as file:
            emojis = filter(lambda emoji: emoji['support'].get('twitter'), json.loads(file.read())['emojis'])
    
        for emoji in emojis:
            yield emoji
    
    return {'emoji_iteratable': get_iteratable}
    
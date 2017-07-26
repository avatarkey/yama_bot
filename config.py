# -*- coding: utf-8 -*-

# Please change TOKEN variable with your bot's token 
# and all the other links with the ones you need.

# The links will later be used to announce changes in the group

import os

TOKEN = os.environ["BOT_TOKEN"]

URL_VK = 'https://api.vk.com/method/wall.get?domain=japanese_underground&count=2&filter=owner'

FILENAME_VK = 'last_known_id.txt'

BASE_POST_URL = 'https://vk.com/wall-39270586_'

creator_id = 111662298
#!/usr/bin/env python3

import requests
import time
import argparse
import os
import json
from utils import *
from dialogue_manager import DialogueManager

from requests.compat import urljoin


class BotHandler(object):
    """
        BotHandler is a class which implements back-end of the bot.
        It has tree main functions:
            'get_updates' — checks for new messages
            'send_message' – posts new message to user
            'get_answer' — computes the most relevant on a user's question
            'download_photo' - asks dialogue manager to download photo
    """

    def __init__(self, token, dialogue_manager):
        self.token = token
        self.api_url = "https://api.telegram.org/bot{}/".format(token)
        self.dialogue_manager = dialogue_manager

    def get_updates(self, offset=None, timeout=30):
        params = {"timeout": timeout, "offset": offset}
        raw_resp = requests.get(urljoin(self.api_url, "getUpdates"), params)
        try:
            resp = raw_resp.json()
        except json.decoder.JSONDecodeError as e:
            print("Failed to parse response {}: {}.".format(raw_resp.content, e))
            return []

        if "result" not in resp:
            return []
        return resp["result"]

    def send_message(self, chat_id, text):
        params = {"chat_id": chat_id, "text": text}
        return requests.post(urljoin(self.api_url, "sendMessage"), params)

    def get_answer(self, photo):
        if photo == '/start':
            return "Hi, I am your project bot. Please upload photo here to receive predicted hashtags"
        return self.dialogue_manager.generate_answer(photo)
    
    def download_photo(self, update):
        return self.dialogue_manager.download_photo(update)


def parse_args():
    # for start from console
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, default='')
    return parser.parse_args()


def main():
    args = parse_args()
    token = args.token

    if not token:
        if not "TELEGRAM_TOKEN" in os.environ:
            print("Please, set bot token through --token or TELEGRAM_TOKEN env variable")
            return
        token = os.environ["TELEGRAM_TOKEN"]

    # ResNeXT is default model
    use_resnext = True
    
    dialogue_manager = DialogueManager(RESOURCE_PATH, use_resnext)
    bot = BotHandler(token, dialogue_manager)
    
    # managing bot chat
    print("Ready to talk!")
    offset = 0
    while True:
        updates = bot.get_updates(offset=offset)
        for update in updates:
            print("An update received.")
            print(update)
            if "message" in update:
                chat_id = update["message"]["chat"]["id"]
                
                # change models or ask for photo
                if "text" in update["message"]:
                    text = update["message"]['text'].lower()
                    
                    if (text == 'use inception') & (use_resnext == True):
                        use_resnext = False
                        
                        dialogue_manager = DialogueManager(RESOURCE_PATH, use_resnext)
                        bot = BotHandler(token, dialogue_manager)
                        bot.send_message(chat_id, 'Changed to Inception')
                        
                    elif (text == 'use inception') & (use_resnext == False):
                        bot.send_message(chat_id, 'Inception is current model')
                        
                    elif (text == 'use resnext') & (use_resnext == True):
                        bot.send_message(chat_id, 'ResNext is current model')
                        
                    elif (text == 'use resnext') & (use_resnext == False):
                        use_resnext = True
                        
                        dialogue_manager = DialogueManager(RESOURCE_PATH, use_resnext)
                        bot = BotHandler(token, dialogue_manager)
                        bot.send_message(chat_id, 'Changed to ResNext')
                        
                    else:
                        bot.send_message(chat_id, "Send me photo to predict Instagram hashtags!")
                        bot.send_message(chat_id, "If you want to change model, type 'use inception' or 'use resnext'")
                          
                # processing photo logic
                if "photo" in update["message"]:

                    photo_saved_path = bot.download_photo(update)
                    answer = bot.get_answer(photo_saved_path)
                    
                    """
                    prediction_text looks like:
                    
                    Top5 tags with numbers of posts: 
                    food (379.8m), nature (500.7m), christmas (146.4m), dessert (52.8m), cake (81m)
                    
                    
                    convenient_tag_string looks like:
                    
                    #food #nature #christmas #dessert #cake
                    
                    """
                    
                    prediction_text, convenient_tag_string = answer
             
                    
                    with open(RESOURCE_PATH['LOGGER_FILE_PATH'], 'a') as f:
                        # for full investigation
                        json.dump({'photo_saved_path':photo_saved_path, 'answer':answer, "update": update}, f)
                        
                    with open(RESOURCE_PATH['SHORT_LOGGER_FILE_PATH'], 'a') as f:
                        # for easy investigation
                        json.dump({'photo_saved_path':photo_saved_path, 'answer':answer}, f)
                        
                    bot.send_message(chat_id, prediction_text)
                    bot.send_message(chat_id, convenient_tag_string)
                    
            offset = max(offset, update['update_id'] + 1)
        time.sleep(1)

if __name__ == "__main__":
    main()

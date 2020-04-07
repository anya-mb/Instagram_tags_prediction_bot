import torch
from torchvision import transforms
from PIL import Image
import numpy as np

import json
import argparse
import os
import requests


BOT_TOKEN = ### Telegram Api Token

class DialogueManager(object):
    def __init__(self, paths, use_resnext, means = np.array([0.485, 0.456, 0.406]),
                 stds = np.array([0.229, 0.224, 0.225])):
        print("Loading resources...")
        
        # model loading
        if use_resnext:
            # loading fine tuned ReNeXT101_32x8d
            # Please refer to "Exploring the Limits of Weakly Supervised Pretraining" 
            # (https://arxiv.org/abs/1805.00932) presented at ECCV 2018 for the details of model training.
            self.predictor_model = torch.load(paths["RESNEXT_MODEL_PATH"])
            input_size = 224
            
        else:
            self.predictor_model = torch.load(paths["INCEPTION_MODEL_PATH"])
            input_size = 299
        
        self.predictor_model.to(device='cpu');
        self.predictor_model.eval()
        
        # transform for received image by Telegram Bot that is used for prediction with model
        self.val_transform = transforms.Compose([
            transforms.Resize((input_size, input_size)),
            transforms.ToTensor(),
            transforms.Normalize(means, stds)
        ])
        
        # all images received by Telegram Bot are saved in this path
        self.path_to_save_images = paths["SAVE_IMAGES_PATH"]
        
        # uploading converters
        # tag2posts is {tag: number of posts with it}
        with open(paths['TAG2POSTS_PATH'], 'r') as f:
            self.tag2posts = json.loads(f.read()) 
        
        # tag2idx is {tag: tag index used for model training}
        with open(paths['TAG2IDX_PATH'], 'r') as f:
            tag2idx = json.loads(f.read()) 
        
        # calculates idx2tag converter from tag2idx
        # as if saving with json indices will be strings not ints
        idx2tag = {}
        for k, v in tag2idx.items():
            idx2tag[v] = k
            
        self.idx2tag = idx2tag
        print('self.idx2tag[5]', self.idx2tag[5]) # checking that it works correct

        print("DialogueManager initialised")
    
    def download_photo(self, photo_info):
            
        CHAT_ID = photo_info["message"]['chat']['id']
        
        # Select highest resolution photo
        file_id = photo_info["message"]["photo"][-1]["file_id"]
        # Get file_path
        photo = get_json('getFile', params={"chat_id": CHAT_ID, "file_id": file_id})
        file_path = photo['result']['file_path']
        # Download photo
        file_name = os.path.basename(file_path)
        response = requests.get('https://api.telegram.org/file/bot%s/%s' % (BOT_TOKEN, file_path))
        
        dst_file_path = os.path.join(self.path_to_save_images, file_name)
        with open(dst_file_path, 'wb') as f:
            f.write(response.content)
        print(u"Downloaded file to {}".format(dst_file_path))
        
        return dst_file_path
        
   

    def generate_answer(self, photo_saved_path):
        # indices of top 5 tags
        top_5 = self.predict_by_model(photo_saved_path)
        
        if top_5 is None:
            bot_answer = ('Wow wow!', '#instagood')
            return bot_answer
        
        # convert to tags words
        top_5_tags_words = [self.idx2tag[ind] for ind in top_5]
        
        # nice representation for Telegram Bot message
        top_5_tags_with_posts = [tag + ' (' + self.tag2posts[tag] + ')' for tag in top_5_tags_words]
        prediction_text = "Top5 tags with numbers of posts: \n"+', '.join(top_5_tags_with_posts)+'\n'
        
        # Instagram like tags (i.e. #nature #travel ...)
        convenient_tag_string = ' '.join(['#'+tag for tag in top_5_tags_words])
        
        print('prediction_text', prediction_text)
           
        return (prediction_text, convenient_tag_string)
        
    
    def predict_by_model(self, photo_saved_path):
        
        img = Image.open(photo_saved_path)
        
        # .convert('RGB') is essential when photos are black and white as well as colorful 
        img = img.convert('RGB')
        
        # applying transformation
        img = self.val_transform(img)
        img = img.unsqueeze(0)
        
        # predict probabilities for every class
        output = self.predictor_model(img)
        
        # selecting top 5 with larger probabilities
        top_5 = np.argsort(output.cpu().detach().numpy()[0])[:-6:-1]
        
        return top_5 # list of 5 tag indices
    
def get_json(method_name, *args, **kwargs):
    return make_request('get', method_name, *args, **kwargs)

def post_json(method_name, *args, **kwargs):
    return make_request('post', method_name, *args, **kwargs)

def make_request(method, method_name, *args, **kwargs):
    response = getattr(requests, method)(
        'https://api.telegram.org/bot%s/%s' % (BOT_TOKEN, method_name),
        *args, **kwargs
    )
    if response.status_code > 200:
        raise DownloadError(response)
    return response.json()
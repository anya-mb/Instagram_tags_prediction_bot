Instagram Hashtags Predictor Bot
----------

This bot predicts Instagram hashtags based on a given photo.

# Project Structure

Bot:

-   dialogue_manager.py
-   main_bot.py
-   utils.py

Data preparation:

-   Instagram_download_photos_and_clean.ipynb
-   preprocessing_cleaning_tags.ipynb

Model training:

-   training_Inception_V3_model.ipynb
-   training_ReNeXT101_32x8d_model.ipynb

# Modules

## dialogue_manager.py

The [DialogueManager](https://github.com/anya-mb/Instagram_tags_prediction_bot/blob/master/bot_architecture/dialogue_manager.py) class handles the interactions with
the user and photo processing to predict hashtags.

Main Components:

-   `download_photo`: Downloads the photo sent by the user.
-   `generate_answer`: Generates a bot\'s response based on the
    predicted hashtags.
-   `predict_by_model`: Predicts the tags using the loaded model.

## main_bot.py

This module manages the back-end of the bot. It initializes the bot,
checks for updates, sends messages, and switches between Inception and
ResNeXT models upon user\'s request.

Main Components:

-   `BotHandler` class: Implements methods to get updates from users,
    send messages, get answers, and download photos.

## utils.py

This module provides the paths for all resources required by the bot.

# Usage

1.  Setup your environment with the necessary libraries and
    dependencies.
2.  Obtain a Telegram API token and replace the placeholder in
    `dialogue_manager.py`.
3.  Run the [main_bot.py](https://github.com/anya-mb/Instagram_tags_prediction_bot/blob/master/bot_architecture/main_bot.py) script.
4.  Start the chat on Telegram with the bot and upload a photo to
    receive predicted Instagram hashtags. Users can also switch between
    models by typing \'use inception\' or \'use resnext\'.

# Notes

For further details on the model training, refer to the Jupyter
notebooks provided in the project.

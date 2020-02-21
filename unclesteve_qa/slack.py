import os
import json
import re
import slack
import requests
from io import BytesIO
from PIL import Image
from collections import defaultdict
from unclesteve_qa.model import USEQAModel

class UncleSteveRTMClient:

    def __init__(self, qa_model_path, always_respond_in=None, respond_to_questions=False, respond_to_mentions=True,
                 respond_to_broadcasts=True, respond_to_im=True, respond_to_img=True):
        # Set variables
        self.always_respond_in = (always_respond_in if always_respond_in is not None else [])
        self.respond_to_questions = respond_to_questions
        self.respond_to_mentions = respond_to_mentions
        self.respond_to_broadcasts = respond_to_broadcasts
        self.respond_to_im = respond_to_im
        self.respond_to_img = respond_to_img

        # The QA model
        self.qa_model = USEQAModel.load(qa_model_path)
        # Some information about my identity (we cache it so we do not have to use the API every time)
        self.my_identity = None
        # Channel data ( we cache it so we do not have to use the API every time)
        self.channel_data = dict()

        slack.RTMClient.run_on(event='message')(self.handle_message)

    def get_channel_data(self, web_client, channel_id):
        # If we do not yet know the channel...
        if channel_id not in self.channel_data:
            # ... ask the API about it.
            self.channel_data[channel_id] = web_client.conversations_info(channel=channel_id)
        return self.channel_data[channel_id]

    def bot_user_id(self, web_client):
        # If we do not yet know our identity...
        if self.my_identity is None:
            # ... ask the API about it.
            self.my_identity = web_client.auth_test()
        return self.my_identity['user_id']

    def handle_message(self, **payload):
        data = payload['data']  # The data
        web_client = payload['web_client']  # The Web Client (to make API requests)

        # Determine some stuff about the data
        channel_id = data['channel']  # The channel id
        text = SlackDataProcessor.get_text(data)  # The (raw) text
        mentions = SlackDataProcessor.get_mentions(data)  # The mentions in the text
        channel_data = self.get_channel_data(web_client, channel_id)  # Some information about the channel
        channel_name = channel_data['channel'].get('name')  # Channel name
        is_instantmessage = channel_data['channel']['is_im']  # Whether or not the message is an IM
        is_thread_message = 'thread_ts' in data  # Whether or not the message is a thread
        channel_in_always_respond = channel_name is not None and channel_name in self.always_respond_in

        # The response
        response = None

        # If 1 file is attached, and no text is supplied...
        if data.get('user') != self.bot_user_id(web_client) and self.respond_to_img and \
                not text and 'files' in data and len(data['files']) == 1:
            # Retrieve file data
            file_data = data['files'][0]
            # Retrieve mime main- and subtype
            mimetype = file_data['mimetype'].split('/')
            # If the main type is an image...
            if mimetype[0] ==  'image':
                # Note, we wrap this clause in a try/except block because there are many things that could go
                # wrong in downloading and/or parsing the image.
                try:
                    # ..., we download the image using the os.environ['SLACK_API_TOKEN'] token. Probably it
                    # would be more elegant to use the web_client token, but I am not entirely sure how to
                    # retrieve it. However, these tokens should always match, so it is not really a problem.
                    response = requests.get(
                        url=file_data['url_private'],
                        headers={
                            'Authorization': 'Bearer %s' % os.environ['SLACK_API_TOKEN']
                        }
                    )
                    # Parse bytes using PIL
                    img = Image.open(BytesIO(response.content))
                    response, distance = self.qa_model.get_image_answer(img)

                except BaseException:
                    # Something went wrong with one of the following:
                    # - Downloading the image
                    # - Opening/Parsing the image in PIL
                    # - Using tesseract OCR to retrieve the text
                    # In any case, we just abort.
                    return

        # We only respond if it is not the bot who is typing, and if the message is a user text message
        elif data.get('user') != self.bot_user_id(web_client) and SlackDataProcessor.is_user_text_message(data):
            # We respond if one of the conditions is satisfied:
            # - It is in a channel where we always respond and is not a thread message,
            # - It is a broadcast message (and parameter is True)
            # - It is an instantmessage (and parameter is True),
            # - The text contains a question mark (and parameter is True), or,
            # - The bot is mentioned (and parameter is True)
            if (channel_in_always_respond and not is_thread_message) or \
                    (self.respond_to_broadcasts and SlackDataProcessor.is_broadcast(data)) or \
                    (self.respond_to_im and is_instantmessage) or \
                    (self.respond_to_questions and '?' in text) or \
                    (self.respond_to_mentions and self.bot_user_id(web_client) in mentions):
                response, distance = self.qa_model.get_answer(text)

        # Respond if we have a response
        if response:
            # Thread is either the original timestamp if there is no thread yet, or the thread_ts
            thread_ts = (data['thread_ts'] if is_thread_message else data['ts'])
            web_client.chat_postMessage(
                channel=channel_id,
                thread_ts=(None if is_instantmessage else thread_ts),
                text=response,
                as_user=True
            )


class SlackDataProcessor:

    def __init__(self, path_to_slack_data: str):
        self.path_to_slack_data = path_to_slack_data
        self.channels = os.listdir(path_to_slack_data)
        self.slack_channel_data = self.parse_slack_data_by_channel()
        self.indexed_messages = self.index_messages_by_user_and_timestamp()


    def parse_slack_data_by_channel(self):
        result = {}
        # Retrieve all channels from dir
        for channel in self.channels:
            channel_messages = []
            # Retrieve directory
            channel_dir = os.path.join(self.path_to_slack_data, channel)
            # Loop through all files (sorted by date)
            for f in sorted(os.listdir(channel_dir)):
                with open(os.path.join(channel_dir, f), encoding='utf8') as f:
                    # Append messages
                    channel_messages.extend(json.load(f))
            # Set result
            result[channel] = channel_messages
        return result

    def index_messages_by_user_and_timestamp(self):
        result = defaultdict(dict)
        for channel in self.channels:

            for message in self.slack_channel_data[channel]:
                if 'user' in message and 'ts' in message:
                    user = message['user']
                    ts = message['ts']
                    result[user][ts] = message
        return result

    def get_message_by_user_and_timestamp(self, user, timestamp):
        try:
            return self.indexed_messages[user][timestamp]
        except KeyError:
            return None

    def get_thread_reply_pairs(self):
        """
        Method that retrieves a list of all thread-answer pairs.
        :return: List of all thread-answer pairs.
        """
        result = []
        for channel in self.channels:
            for message in self.slack_channel_data[channel]:
                # If there is text, and there are replies
                if self.is_user_text_message(message) and 'replies' in message:
                    for reply in message['replies']:
                        # Retrieve the reply message
                        reply_message = self.get_message_by_user_and_timestamp(reply['user'], reply['ts'])
                        # Add it if it contains text
                        if reply_message and self.is_user_text_message(reply_message):
                            result.append((message['text'], reply_message['text']))
        return result

    def get_context_answer_pairs(self, max_td=600, max_occurrence_rate=1, include_self=True):
        """
        Method that extracts all context-answer pairs from all the Slack data.
        A context-answer pair is a pair of strings for which the answer can be considered
        an answer to -some- question in the given context.
        :param max_td: Max time-difference for which context may appear before answer.
        :param max_occurrence_rate: Maximum amount of times we allow a message to appear with a context pair.
        :param include_self: Whether or not a message may also appear as its own context.
        :return: List of all pairs
        """
        result = []
        for channel in self.channels:
            for i, message in enumerate(self.slack_channel_data[channel]):
                # If there is text...
                if self.is_user_text_message(message):
                    num_added = 0
                    if include_self and num_added < max_occurrence_rate:
                        result.append((message['text'], message['text']))
                        num_added += 1
                    # Iterate over previous messsages
                    for previous_message in reversed(self.slack_channel_data[channel][:i]):
                        time_delta = float(message['ts']) - float(previous_message['ts'])
                        if time_delta > max_td or num_added >= max_occurrence_rate:
                            break
                        if self.is_user_text_message(previous_message):
                            # Message is older than max_td, but we include it anyway
                            result.append((previous_message['text'], message['text']))
                            num_added += 1

        return result

    @staticmethod
    def is_user_text_message(message: dict):
        # We check for message subtype, since it can be one of the following:
        # {'sh_room_created', 'channel_unarchive', 'me_message', 'tombstone', 'channel_purpose', 'channel_leave',
        #  'bot_message', 'slackbot_response', 'reminder_add', 'channel_topic', 'channel_join', 'channel_archive',
        #  'channel_name', 'file_comment', 'thread_broadcast', 'reply_broadcast', 'pinned_item'}
        return 'text' in message and len(message['text'])>0 and 'subtype' not in message

    @classmethod
    def get_text(cls, message: dict, keep_mentions=False, keep_emojis=False, keep_links=False):
        """
        A simple recursive method to get the raw text out of a message. This method gives us the option
        to strip mentions, emojis, links, etc.
        :param message:
        :param keep_mentions:
        :param keep_emojis:
        :param keep_links:
        :return:
        """
        def parse_elements(elements):
            text = ''
            for element in elements:
                if 'elements' in element:
                    text += parse_elements(element['elements'])
                if element['type'] == 'text':
                    text += element['text']
                if element['type'] == 'emoji' and keep_emojis:
                    text += ':' + element['name'] + ':'
                if element['type'] == 'user' and keep_mentions:
                    text += '<@' + element['user_id'] + '>'
                if element['type'] == 'link' and keep_links:
                    text += '<' + element['url'] + '>'
            return text
        if 'blocks' in message:
            return parse_elements(message['blocks']).strip()
        else:
            return cls.get_text_(message.get('text'))

    @classmethod
    def get_text_(cls, text: str, keep_mentions=False, keep_emojis=False, keep_links=False):
        # If None is supplied, we return the empty string
        if text is None:
            return ''

        # * = bold, _ = italic, ~ = strikethrough, ` = code
        replacements = [('*', ''), ('_', ''), ('~', ''), ('`', '')]
        if not keep_mentions:
            text = re.sub('<@[^>]*>', '', text)
        if not keep_links:
            text = re.sub('<[^>]*>', '', text)
        if not keep_emojis:
            text = re.sub(':[^:]*:', '', text)
        for before, after in replacements:
            text = text.replace(before, after)
        return text.strip()

    @classmethod
    def is_broadcast(cls, message: dict):
        def contains_broadcast(elements):
            for element in elements:
                if 'elements' in element:
                    return contains_broadcast(element['elements'])
                if element['type'] == 'broadcast':
                    return True
            return False
        if 'blocks' in message:
            return contains_broadcast(message['blocks'])
        else:
            return cls.is_broadcast_(message.get('text'))

    @classmethod
    def is_broadcast_(cls, text: str):
        # If no text is given, it is no broadcast
        if text is None:
            return False

        return ('<!channel>' in text) or ('<!here>' in text)

    @classmethod
    def get_mentions(cls, message: dict):
        """
        Just a simple method to retrieve all mentions from messages.
        :param message:
        :return:
        """
        def get_user_elements(elements):
            users = []
            for element in elements:
                if 'elements' in element:
                    users += get_user_elements(element['elements'])
                if element['type'] == 'user':
                    users.append(element['user_id'])
            return users
        if 'blocks' in message:
            return get_user_elements(message['blocks'])
        else:
            return cls.get_mentions_(message.get('text'))

    @classmethod
    def get_mentions_(cls, text: str):
        # If no text is given, it contains no mentions
        if text is None:
            return []
        return re.findall('<@([^>]*)>', text)
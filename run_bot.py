from unclesteve_qa.slack import UncleSteveRTMClient
import slack
import os
from dotenv import load_dotenv
load_dotenv()

# Create RTM Client
rtm_client = slack.RTMClient(token=os.environ["SLACK_API_TOKEN"])

# Init RTM Client
UncleSteveRTMClient(
    qa_model_path=os.path.join('model', 'slackbot_large.model'),
    respond_to_questions=True,
    respond_to_broadcasts=True,
    respond_to_im=True,
    respond_to_mentions=True,
    respond_to_img=True,
    # always_respond_in=['announcements']
)

# Run it
print('Running')
rtm_client.start()
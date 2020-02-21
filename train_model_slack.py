import os

from unclesteve_qa.model import USEQAModel
from unclesteve_qa.slack import SlackDataProcessor

slack_data_processor = SlackDataProcessor('data_example')

context_answers = slack_data_processor.get_context_answer_pairs(max_occurrence_rate=1) +\
                  slack_data_processor.get_thread_reply_pairs()

model = USEQAModel()
model.train(
    context_answers=context_answers,
    text_processing_func=SlackDataProcessor.get_text_,
    batch_size=100
)

model.save(os.path.join('model', 'slackbot_large.model'))
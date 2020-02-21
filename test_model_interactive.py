import os

from unclesteve_qa.model import USEQAModel

model =  USEQAModel.load(os.path.join('model', 'slackbot_large.model'))
while True:
    q = input('Vraag:')
    print(model.get_answer(q))

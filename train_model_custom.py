import os

from unclesteve_qa.model import USEQAModel

answers = [
    'Hoi ik ben Max',
    'Ik ben 33 jaar oud',
    'Ik hou van pindakaas.'
]

model = USEQAModel()
model.train(
    context_answers=list(zip(answers, answers)),
    batch_size=100
)

model.save(os.path.join('model', 'slackbot_custom.model'))
import os

from unclesteve_qa.model import USEQAModel

model =  USEQAModel.load(os.path.join('model', 'slackbot_large.model'))

test_sentences = [
    'Reminder! :santa::skin-tone-3: Volgende week donderdag (19/12) organiseren we de foute kerst-outfit lunch. Dit jaar wint meest foute outfit een Nintendo Classic Mini. Je hebt nog iets meer dan een week om de meest foute en originele outfit te bestellen of te maken zodat deze op tijd bezorgd wordt/klaar is! :parrotchristmas:',
    'ABCD meeting in de boardroom om 16h00',
    'Budget is er!!',
    ':zap:️Newsflash gemist gisteren? Geen stress want je kan hem nu terugkijken in de Triple App.',
    'Groot compliment aan het Ziggo team, vrijdag zullen we deze release op gepaste wijzen vieren.',
    ' is er iemand die een goede tool weet voor screen recordings maken en delen? Asking for a tester'
]
for test_sentence in test_sentences:
    answer = model.get_answer(test_sentence)
    print(test_sentence + '\n--> ' + str(answer) + '\n---')

# Installeren
Installeren van `requirements.txt`:
* `pip install -r requirements.txt`

Note: Bot werkt alleen op Linux.

# Trainen / Testen
De volgende bestanden kunnen gebruikt worden voor het trainen en testen van de bot:
* `train_model_slack.py`: Hiermee kan een nieuwe Slack bot getrained worden. Wat benodigd is, 
is een uitdraai van alle Slack data in een folder. In dit geval is een voorbeeld geplaatst in de map `data_example`.
* `train_model_custom.py`: Hiermee kan een nieuwe Slack bot getrained worden op basis van een lijst van zinnen.
Deze kan je zelf aanleveren.
* `test_model_interactive.py`: Hiermee kan je de bot testen door er vragen aan te stellen.
* `test_model_auto.py`: Hiermee kan je testen wat de bot zou zeggen op basis van vragen die mensen zouden kunnen stellen.


# Uitvoeren van de bot
Uitvoeren van de bot op Slack kan door middel van het uitvoeren van het script `run_bot.py`. 
Tevens kunnen daar opties worden aangepast over op welke berichten/channels/etc. de bot zou moeten antwoorden.
* `always_respond_in`: Lijst van channels waar de bot altijd zou moeten reageren (op elk bericht). Bedoeld voor testen.
* `respond_to_questions`: True/False als we willen dat de bot reageert op vragen (berichten met een vraagteken).
* `respond_to_mentions`: True/False als we willen dat de bot reageert op mentions.
* `respond_to_broadcasts`: True/False als we willen dat de bot reageert op broadcasts.
* `respond_to_im`: True/False als we willen dat de bot reageert op instant messages.
* `respond_to_img`: True/False als we willen dat de bot reageert op images.

# Deployen
Bouwen en uitvoeren van de bot kan m.b.v. docker:
1. Bouwen: `docker build -t <naam> .`
2. Uitvoeren: `docker run -e SLACK_API_TOKEN=<slack_api_token> <naam>`

Vervang `<naam>` met je gewenste naam, en vervang `<slack_api_token>` met jouw slack API token. Voor meer informatie, 
bekijk de [Slack pagina](https://api.slack.com/tokens).


© 2020, [M.Knobbout](mailto:m.knobbout@wearetriple.com) / [Triple](https://www.wearetriple.com)
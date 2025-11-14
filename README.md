# supahchatbot_airs_api
Test app for the Prisma AIRS API

Clone this repo to user Ubuntu box

Install dotenv and openai python libraries with pip pip install dotenv pip install openai

Deploy your LLM with Azure AI Foundry

Get API key, endpoint, api version information from the Azure AI Foundry

Set API keys and API endpoint to app.py file

Modify app.py with your api version information.

Install Screen "sudo apt install screen"

Start screen with "screen -S chatbot"

Fire up the app with "flask run -p 8080 --host=0.0.0.0"

Detach from the screen with ctrl + a,d

Now the Super Chatbot should be accessible via TCP port 8080

This version is responding with JSON. JSON response is needed when you test the Prisma AIRS Red Teaming.

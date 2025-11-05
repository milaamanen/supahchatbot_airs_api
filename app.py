import os
import dotenv
from flask import Flask, render_template, request
from openai import AzureOpenAI
import httpcore
import requests, json

dotenv.load_dotenv()



app = Flask(__name__)

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint="#ENDPOINT#",
    api_key="#AZUREAPIKEY#"
)

security_profile_name = "DemoApp1"
url = "https://service.api.aisecurity.paloaltonetworks.com/v1/scan/sync/request"
header = {'x-pan-token': '#AIRS_API_KEY#',
          'Content-Type': 'application/json',
          'Accept': 'application/json'}

error_for_blocked_prompt = "Prompt Blocked by AIRS Api"
error_for_blocked_reply ="Reply Blocked by AIRS API"
error_for_blocked_by_airs_fw= "Blocked by AI Runtime Security Firewall"

system_prompt = {
        "role": "system",
        "content": "You are the best chatbot in the world!"
}

def ScanPrompt(user_input):
    json_object = {
      "contents": [
        {
          "prompt": user_input
        }
      ],
      "ai_profile": {
        "profile_name": security_profile_name
      }
    }
    response = requests.post(url, json = json_object, headers = header)
    json_data = json.loads(response.text)
    print (json_data)
    recommendedAction = json_data['action']
    print("The recommended action for the prompt is: " + recommendedAction + ".")
    return recommendedAction

def ScanResponse(user_input):
    json_object = {
      "contents": [
        {
          "response": user_input
        }
      ],
      "ai_profile": {
        "profile_name": security_profile_name
      }
    }
    response = requests.post(url, json = json_object, headers = header)
    json_data = json.loads(response.text)
    recommendedAction = json_data['action']
    print("The recommended action for the LLM reply is: " + recommendedAction + ".")
    return recommendedAction

conversation = [
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    global conversation
    if user_input == "" or user_input is None:
      return "Empty"
    else:
      conversation.append({"role": "user", "content": user_input})
      print (user_input)
      action=ScanPrompt(user_input)
      if action == "allow":
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=conversation
            )
        except:
            print("RemoteProtocolError")
            conversation = []
            conversation.append(system_prompt)
            reply = error_for_blocked_by_airs_fw
            json_reply = {
                           "response": reply
                           }
            print (json_reply)
            return json_reply
        else:
            reply = response.choices[0].message.content
            check_reply = ScanResponse(reply)
            if check_reply == "allow":
              json_reply = {
                           "response": reply,
                           }
              print (json_reply)
              return json_reply
              
            else:
              json_reply = {
                           "response": error_for_blocked_reply,
                           }
              print (json_reply)
              return json_reply
          
      else:
        reply = error_for_blocked_prompt

    conversation.append({"role": "assistant", "content": reply})
    json_reply = {
    "response": reply,
    }
    print (json_reply)
    return json_reply
    #return reply

if __name__ == '__main__':
    conversation.append(system_prompt)
    app.run(debug=True,host="0.0.0.0", port=8080)

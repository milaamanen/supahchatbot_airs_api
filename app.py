import os
import dotenv
from flask import Flask, render_template, request, session # <-- Import session
import uuid # <-- Import uuid to generate session IDs
from openai import AzureOpenAI
import httpcore
import requests, json

dotenv.load_dotenv()

app = Flask(__name__)
# A secret key is required to use Flask sessions
app.secret_key = os.urandom(24) 

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

# This function runs before each request to initialize the session
@app.before_request
def ensure_session():
    # Create a unique session ID for the user if it doesn't exist
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        print(f"New session created with ID: {session['session_id']}")
    
    # Create a conversation history for the user if it doesn't exist
    if 'conversation' not in session:
        session['conversation'] = []
        session['conversation'].append(system_prompt)

def ScanPrompt(user_input, session_id):
    json_object = {
        "session_id": session_id, # <-- Added session_id
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

def ScanResponse(user_input, session_id):
    json_object = {
        "session_id": session_id, # <-- Added session_id
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


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message")
    
    # Get session_id from the user's session
    session_id = session['session_id'] 

    if user_input == "" or user_input is None:
        return "Empty"
    else:
        # Use session['conversation'] instead of global conversation
        session['conversation'].append({"role": "user", "content": user_input})
        print (user_input)
        
        # Pass session_id to ScanPrompt
        action=ScanPrompt(user_input, session_id)
        
        if action == "allow":
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=session['conversation'] # Use session conversation
                )
            except:
                print("RemoteProtocolError")
                # Reset the session's conversation
                session['conversation'] = [] 
                session['conversation'].append(system_prompt)
                reply = error_for_blocked_by_airs_fw
                json_reply = {
                            "response": reply
                            }
                print (json_reply)
                return json_reply
            else:
                reply = response.choices[0].message.content
                
                # Pass session_id to ScanResponse
                check_reply = ScanResponse(reply, session_id)
                
                if check_reply == "allow":
                    json_reply = {
                                "response": reply,
                                }
                    print (json_reply)
                
                else:
                    reply = error_for_blocked_reply # <-- Set reply to the error message
                    json_reply = {
                                "response": error_for_blocked_reply,
                                }
                    print (json_reply)
                
        else:
            reply = error_for_blocked_prompt

    # Append the final reply (or error) to the session conversation
    session['conversation'].append({"role": "assistant", "content": reply})
    json_reply = {
        "response": reply,
    }
    print (json_reply)
    return json_reply


if __name__ == '__main__':
    # No need to append system_prompt here, @before_request handles it
    app.run(debug=True,host="0.0.0.0", port=8080)

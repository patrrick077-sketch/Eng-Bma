import time
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# --- FIX: Display Burmese/Unicode characters correctly ---
app.config['JSON_AS_ASCII'] = False

# --- Configuration ---
INVOKE_URL = 'https://integrate.api.nvidia.com/v1/chat/completions'
API_KEY = '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'

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

SYSTEM_PROMPT = (
    "You are an Biology X English → Burmese vocabulary translator. "
    "Whenever I send an English word or phrase, respond in this exact format: "
    "Word Pronunciation using IPA Simple Burmese pronunciation written in Burmese letters "
    "Part of Speech (n, v, adj, adv, etc.) Burmese meaning One simple English example sentence "
    "Burmese translation of the example sentence Format the answer exactly like this: "
    "Word 🔊 Pronunciation: /IPA/ → Burmese pronunciation 📚 Part of Speech: n / v / adj / adv (write the correct one) "
    "🇲🇲 Meaning: Burmese translation 📘 Example sentence: English sentence. → Burmese translation. "
    "Rules: Keep explanations short and clear. Always include pronunciation. Always include part of speech. "
    "Always include one example sentence. If the word has multiple parts of speech, show each clearly. "
    "If the spelling is wrong, correct it first and then answer. I will only send words or short phrases. "
    "Always follow this format."
)

@app.route('/chat', methods=['GET', 'POST'])
def chat():
    # 1. Get the user prompt
    if request.method == 'GET':
        user_prompt = request.args.get('prompt')
    else: # POST
        data = request.get_json(silent=True) or request.form
        user_prompt = data.get('prompt')

    if not user_prompt:
        return jsonify({"error": "Please provide a 'prompt' parameter."}), 400

    # 2. Construct the Payload
    payload = {
        "model": "z-ai/glm5",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 1,
        "top_p": 1,
        "max_tokens": 16384,
        "stream": False,
        "chat_template_kwargs": {
            "enable_thinking": False,
            "clear_thinking": True
        }
    }

    # 3. Send Request and Measure Time
    try:
        start_time = time.time() # Start timer
        response = requests.post(INVOKE_URL, headers=HEADERS, json=payload)
        end_time = time.time()   # End timer
        
        response.raise_for_status()
        
        response_data = response.json()

        # 4. Extract Usage Stats & Calculate Speed
        usage = response_data.get('usage', {})
        completion_tokens = usage.get('completion_tokens', 0)
        prompt_tokens = usage.get('prompt_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)
        
        # Calculate duration and tokens per second
        latency = round(end_time - start_time, 2)
        tokens_per_second = 0
        if latency > 0 and completion_tokens > 0:
            tokens_per_second = round(completion_tokens / latency, 2)

        # 5. Return Full Detailed Response
        if 'choices' in response_data and len(response_data['choices']) > 0:
            ai_message = response_data['choices'][0]['message']['content']
            
            return jsonify({
                "status": "success",
                "response": {
                    "Model": "M.H.M Ai",
                    "Response": ai_message
                },
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "latency_seconds": latency,
                    "tokens_per_second": tokens_per_second
                }
            })
        else:
            return jsonify({"error": "Unexpected response structure", "details": response_data}), 500

    except requests.exceptions.HTTPError as err:
        return jsonify({"error": "API Request Failed", "details": str(err)}), 500
    except Exception as e:
        return jsonify({"error": "Server Error", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

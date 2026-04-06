import time
from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# ✅ FIX: Proper Unicode support (Flask 2.3+)
app.json.ensure_ascii = False


# --- Configuration ---
INVOKE_URL = 'https://integrate.api.nvidia.com/v1/chat/completions'
API_KEY = 'YOUR_API_KEY_HERE'  # 🔒 Replace with your real key

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

SYSTEM_PROMPT = (
    "You are an Biology X English → Burmese vocabulary translator. "
    "Whenever I send an English word or phrase, respond in this exact format: "
    "Word 🔊 Pronunciation: /IPA/ → Burmese pronunciation "
    "📚 Part of Speech: n / v / adj / adv "
    "🇲🇲 Meaning: Burmese translation "
    "📘 Example sentence: English sentence. → Burmese translation. "
    "Rules: Keep explanations short and clear. Always include pronunciation. "
    "Always include part of speech. Always include one example sentence. "
    "If the word has multiple parts of speech, show each clearly. "
    "If the spelling is wrong, correct it first and then answer. "
    "Always follow this format."
)


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    # 1. Get user input
    if request.method == 'GET':
        user_prompt = request.args.get('prompt')
    else:
        data = request.get_json(silent=True) or request.form
        user_prompt = data.get('prompt') if data else None

    if not user_prompt:
        return jsonify({"error": "Please provide a 'prompt' parameter."}), 400

    # 2. Build payload
    payload = {
        "model": "z-ai/glm5",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 1,
        "top_p": 1,
        "max_tokens": 1024,
        "stream": False,
        "chat_template_kwargs": {
            "enable_thinking": False,
            "clear_thinking": True
        }
    }

    try:
        # 3. Send request
        start_time = time.time()
        response = requests.post(INVOKE_URL, headers=HEADERS, json=payload, timeout=30)
        end_time = time.time()

        response.raise_for_status()
        response_data = response.json()

        # 4. Extract usage
        usage = response_data.get('usage', {})
        completion_tokens = usage.get('completion_tokens', 0)
        prompt_tokens = usage.get('prompt_tokens', 0)
        total_tokens = usage.get('total_tokens', 0)

        latency = round(end_time - start_time, 2)
        tokens_per_second = (
            round(completion_tokens / latency, 2)
            if latency > 0 and completion_tokens > 0 else 0
        )

        # 5. Extract AI response
        if 'choices' in response_data and response_data['choices']:
            ai_message = response_data['choices'][0]['message']['content']

            # ✅ Clean output
            ai_message = ai_message.strip()

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
            return jsonify({
                "error": "Unexpected response structure",
                "details": response_data
            }), 500

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out"}), 504

    except requests.exceptions.HTTPError as err:
        return jsonify({
            "error": "API Request Failed",
            "details": str(err),
            "response_text": response.text
        }), 500

    except Exception as e:
        return jsonify({
            "error": "Server Error",
            "details": str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

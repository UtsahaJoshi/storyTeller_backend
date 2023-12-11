from pathlib import Path

import openai
from flask import Flask, jsonify, request
from flask_cors import CORS

# Set your OpenAI API key
openai.api_key = 'your API KEY'

app = Flask(__name__)
CORS(app)

client = openai.OpenAI(api_key=openai.api_key)


@app.route('/generate-start', methods=['POST'])
def generate_start():
    text = request.json['text']
    response = client.chat.completions.create(
        model="gpt-4",  # Specify the model
        messages=[
            {"role": "system", "content": "Write 10 lines of a story according to the concept I provide. Make it exciting and interesting. Also generate four possible choices (key-value pairs) for the next part of the story and send the story_text and choices as json data (please re-check if its proper json format and only send back)."},
            {"role": "user", "content": text}
        ]
    )
    print(response.choices[0].message.content)
    return jsonify({"story": response.choices[0].message.content})


@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    text = request.json['text']
    static_dir = Path(__file__).parent / "static"
    speech_file_path = static_dir / "speech.mp3"

    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    response.stream_to_file(speech_file_path)

    with open("./static/speech.mp3", "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format='verbose_json'
        )

    print(transcript)

    # Extract word-timestamp data
    word_timestamps = [
        {"word": segment['text'], "start": segment['start'], "end": segment['end']}
        for segment in transcript.segments
    ]

    print(word_timestamps)

    # Assuming you have a way to serve static files,
    # and 'speech.mp3' is accessible via a URL
    audio_url = f"http://localhost:5000/static/{speech_file_path.name}"

    return jsonify({"audio_url": audio_url, "word_timestamps": word_timestamps})


@app.route('/generate-image', methods=['POST'])
def generate_image():
    gen_prompt = """
    Create an image that vividly illustrates the following narrative, with a 
    focus on central composition suitable for both desktop and mobile screens with a 
    16:9 aspect ratio. The main characters and pivotal elements of the story should be prominently 
    positioned in the center of the image to ensure visibility on different screen sizes. 
    The background should subtly complement the story's theme, adding atmospheric context 
    without overshadowing the central subjects. The image should capture the essence of the story, 
    highlighting key emotions or actions central to the narrative. 
    Make sure the central area of the image contains the core visual elements to remain 
    clearly visible on narrower screens. Please include no texts in the image strictly.
    """

    text = request.json['text']
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=text + gen_prompt,
            n=1,
            size="1792x1024",
            quality="standard"
        )
        image_url = response.data[0].url
        print('image_url', image_url)
        return jsonify({"image_url": image_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

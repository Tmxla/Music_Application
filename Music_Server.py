from flask import Flask, request, jsonify
import soundfile as sf
import sounddevice as sd
import subprocess
import os
import requests

app = Flask(__name__)

AUDD_API_KEY = "너의_audd_api_key"

def convert_wav_to_mp3(wav_file, mp3_file):
    subprocess.run(['ffmpeg', '-y', '-i', wav_file, mp3_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def recognize_song_audd(file_path):
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'api_token': AUDD_API_KEY, 'return': 'spotify'}
        response = requests.post('https://api.audd.io/', data=data, files=files)

    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'API request failed'}

@app.route('/analyze', methods=['POST'])
def analyze_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file uploaded'}), 400

    audio_file = request.files['audio']
    wav_path = 'temp.wav'
    mp3_path = 'recorded.mp3'
    audio_file.save(wav_path)

    convert_wav_to_mp3(wav_path, mp3_path)
    result = recognize_song_audd(mp3_path)
    track_info = result.get('result', {})

    # clean up
    os.remove(wav_path)
    os.remove(mp3_path)

    return jsonify({
        "title": track_info.get("title", "알 수 없음"),
        "artist": track_info.get("artist", "알 수 없음"),
        "cover": track_info.get("spotify", {}).get("album", {}).get("images", [{}])[0].get("url", ""),
    })

if __name__ == '__main__':
    app.run(debug=True)
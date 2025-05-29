# 🎧 AudD + Spotify 음악 인식 통합 코드

import sounddevice as sd
import soundfile as sf
import subprocess
import requests
import base64
import json
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy

# 🔧 Spotify API 설정
SPOTIFY_CLIENT_ID = "04df9d7a817d4709a27eee2e1ecfb2f2"
SPOTIFY_CLIENT_SECRET = "d36b326fc5df4a97b3ba1a96f13280a2"

# 🔑 AudD API Key
AUDD_API_KEY = "757a1dc15f25bd48595392e44ca2acb6"


def record_audio_mp3(filename="recorded.mp3", duration=8, samplerate=44100):
    temp_wav = "temp.wav"
    print("🎙 녹음 시작...")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
    sd.wait()
    sf.write(temp_wav, recording, samplerate)
    print("✅ 녹음 완료: ", temp_wav)

    subprocess.run(["ffmpeg", "-y", "-i", temp_wav, filename], check=True)
    print("✅ MP3 변환 완료: ", filename)
    return filename


def recognize_with_audd(file_path):
    print("🔍 AudD API로 음악 인식 중...")
    url = 'https://api.audd.io/'
    with open(file_path, 'rb') as f:
        files = {
            'file': f
        }
        data = {
            'api_token': AUDD_API_KEY,
            'return': 'spotify'
        }
        response = requests.post(url, data=data, files=files)
    if response.status_code != 200:
        print("❌ AudD API 실패:", response.status_code)
        return None
    return response.json()


def search_spotify(query):
    print(f"🔎 Spotify에서 '{query}' 검색 중...")
    auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    result = sp.search(q=query, limit=1, type='track')
    if result['tracks']['items']:
        track = result['tracks']['items'][0]
        return {
            '제목': track['name'],
            '아티스트': track['artists'][0]['name'],
            '앨범': track['album']['name'],
            '미리듣기': track['preview_url'],
            '앨범커버': track['album']['images'][0]['url']
        }
    else:
        return None


if __name__ == "__main__":
    file = record_audio_mp3(duration=8)
    audd_result = recognize_with_audd(file)

    try:
        title = audd_result['result']['title']
        artist = audd_result['result']['artist']
        print(f"🎵 인식된 곡: {artist} - {title}")

        track_info = search_spotify(f"{title} {artist}")
        if track_info:
            print("🎧 Spotify 정보:")
            for k, v in track_info.items():
                print(f"{k}: {v}")
        else:
            print("❌ Spotify에서 정보를 찾을 수 없습니다.")
    except Exception as e:
        print("❌ 음악 인식 실패 또는 AudD 응답 오류:", e)
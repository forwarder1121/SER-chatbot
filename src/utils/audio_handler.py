import speech_recognition as sr
from pydub import AudioSegment
import io
import streamlit as st

def convert_audio_to_text(wav_audio_data, language='ko-KR'):
    """음성 데이터를 텍스트로 변환하는 함수"""
    try:
        # WAV 데이터를 AudioSegment로 변환
        audio = AudioSegment.from_file(io.BytesIO(wav_audio_data), format="wav")

        # 파일 정보 디버깅 (콘솔 출력)
        print(f"Audio Info: Channels={audio.channels}, Frame Rate={audio.frame_rate}, Duration={len(audio)}ms")

        # 오디오를 16kHz, 모노로 표준화
        audio = audio.set_frame_rate(16000).set_channels(1)

        # 음성이 너무 짧은 경우 패딩 추가
        if len(audio) < 1000:  # 1초 미만인 경우
            silence = AudioSegment.silent(duration=1000 - len(audio))
            audio = audio + silence

        # Google API가 처리할 수 있는 형식으로 변환
        audio_file = io.BytesIO()
        audio.export(audio_file, format="wav")
        audio_file.seek(0)

        # 음성 인식
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data, language=language)
        return text
    except sr.UnknownValueError:
        return None
    except Exception as e:
        print(f"음성 인식 중 오류 발생: {e}")  # 콘솔에 오류 출력
        return None


def process_audio_input(wav_audio_data, language_options=('ko-KR', 'en-US')):
    """음성 입력을 처리하고 결과를 반환하는 함수"""
    if wav_audio_data is not None:
        # 음성 변환
        for language in language_options:
            try:
                # 음성 인식
                audio_text = convert_audio_to_text(wav_audio_data, language=language)
                if audio_text:
                    return audio_text, language
            except Exception:
                continue  # 다음 언어로 시도

        # 텍스트 변환 실패
        return None, None

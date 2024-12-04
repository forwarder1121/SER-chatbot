from datetime import datetime
import streamlit as st
import torch
import torchaudio
import os
from transformers import AutoModelForAudioClassification, AutoProcessor
import torchaudio.transforms as T
from src.core.services.chatbot_service import ChatbotService
from src.app.config import OpenAIConfig
from src.utils.audio_handler import process_audio_input
from src.components.message_display import apply_chat_styles, display_message, get_emotion_color
from streamlit_webrtc import webrtc_streamer, WebRtcMode
import queue
import threading
import wave
import pyaudio
from PIL import Image

# 음성 감정 인식 모델 설정
model_name = "forwarder1121/ast-finetuned-model"
processor = AutoProcessor.from_pretrained(model_name)
model = AutoModelForAudioClassification.from_pretrained(model_name)

# 감정 매핑
EMOTION_MAPPING = {
    0: "Anger",
    1: "Disgust", 
    2: "Fear",
    3: "Happy",
    4: "Neutral",
    5: "Sad"
}

def process_audio(waveform, target_sample_rate=16000, target_length=16000):
    """Process audio to correct format."""
    try:
        if waveform.shape[0] > 1:  # 다채널 오디오인 경우 평균 처리
            waveform = torch.mean(waveform, dim=0, keepdim=True)

        if waveform.shape[1] > 0:
            current_sample_rate = target_sample_rate
            if current_sample_rate != target_sample_rate:
                resampler = T.Resample(orig_freq=current_sample_rate, new_freq=target_sample_rate)
                waveform = resampler(waveform)

        if waveform.shape[1] < target_length:
            padding_length = target_length - waveform.shape[1]
            waveform = torch.nn.functional.pad(waveform, (0, padding_length))
        else:
            start = (waveform.shape[1] - target_length) // 2
            waveform = waveform[:, start:start + target_length]

        return waveform
    except Exception as e:
        st.error(f"Error in audio processing: {str(e)}")
        return None

def predict_audio_emotion(audio_path):
    """Predict emotion from audio file."""
    try:
        waveform, sample_rate = torchaudio.load(audio_path)
        processed_waveform = process_audio(waveform, target_sample_rate=16000)

        if processed_waveform is None:
            return None

        inputs = processor(processed_waveform.squeeze(), sampling_rate=16000, return_tensors="pt")

        with torch.no_grad():
            outputs = model(**inputs)
        
        predicted_class_idx = outputs.logits.argmax(-1).item()

        if predicted_class_idx in EMOTION_MAPPING:
            return EMOTION_MAPPING[predicted_class_idx]
        return None

    except Exception as e:
        st.error(f"Error in emotion prediction: {str(e)}")
        return None

def update_conversation_stats(emotion: str):
    """Update conversation statistics based on the detected emotion."""
    st.session_state.conversation_stats['total'] += 1
    if emotion in ['Happy', 'Neutral']:
        st.session_state.conversation_stats['positive'] += 1
    elif emotion in ['Anger', 'Disgust', 'Fear', 'Sad']:
        st.session_state.conversation_stats['negative'] += 1

def handle_audio_upload(uploaded_audio):
    """Handle audio file upload and emotion prediction."""
    try:
        temp_file_path = "temp_audio.wav"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_audio.getbuffer())

        with st.spinner('음성 분석 중...'):
            # 텍스트 변환
            audio_text, detected_language = process_audio_input(
                uploaded_audio.read(),
                language_options=('ko-KR', 'en-US')
            )
            
            # 감정 분석
            audio_emotion = predict_audio_emotion(temp_file_path)

            # 메시지 추가
            current_time = datetime.now().strftime('%p %I:%M')

            if audio_emotion:
                # `current_emotion` 업데이트
                st.session_state.current_emotion = audio_emotion

                # 텍스트와 감정 표시
                if audio_text:
                    st.session_state.messages.append({
                        "role": "user",
                        "content": f"[음성 파일이 업로드됨] {audio_text}",
                        "emotion": audio_emotion,
                        "timestamp": current_time
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"음성에서 감지된 텍스트는 '{audio_text}'이며, 감정은 '{audio_emotion}'입니다.",
                        "timestamp": current_time
                    })
                else:
                    st.session_state.messages.append({
                        "role": "user",
                        "content": "[음성 파일이 업로드됨]",
                        "emotion": audio_emotion,
                        "timestamp": current_time
                    })
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"음성에서 감지된 감정은 '{audio_emotion}'입니다.",
                        "timestamp": current_time
                    })

                # 통계 업데이트
                update_conversation_stats(audio_emotion)

        # 파일 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        # 새로고침으로 즉시 반영
        st.rerun()

    except Exception as e:
        st.error(f"음성 처리 중 오류가 발생했습니다: {str(e)}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return False



def main():
    st.set_page_config(
        page_title="감정인식 챗봇",
        page_icon="🤗",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 커스텀 스타일 적용
    apply_chat_styles()

    # 세션 상태 초기화
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.chatbot_service = ChatbotService(OpenAIConfig())
        st.session_state.messages = [{
            'role': 'assistant',
            'content': "안녕하세요! 오늘 하루는 어떠셨나요? 기분이나 감정을 자유롭게 이야기해주세요. 텍스트로 입력하거나 음성 파일을 업로드해주세요. 😊",
            'timestamp': datetime.now().strftime('%p %I:%M')
        }]
        st.session_state.last_uploaded_audio = None
        st.session_state.current_emotion = "분석된 감정 없음"
        st.session_state.conversation_stats = {
            'total': 0,
            'positive': 0,
            'negative': 0
        }

    # 음성 녹음을 위한 상태 변수
    if 'audio_recorder_state' not in st.session_state:
        st.session_state.audio_recorder_state = False
        st.session_state.audio_queue = queue.Queue()

    # 사이드바
    with st.sidebar:
        st.title("감정인식 챗봇 🏠")

        st.markdown("### 사용 방법")
        st.markdown("""
        1. 채팅창에 현재 기분이나 근황을 입력하세요.
        2. 음성 파일을 업로드하여 감정을 분석할 수 있습니다.
        3. 챗봇이 감정을 분석하고 공감적인 대화를 제공합니다.
        4. 필요한 경우 적절한 조언이나 위로를 받을 수 있습니다.
        """)

        # 현재 감정 상태 표시
        if 'current_emotion' in st.session_state:
            st.markdown("### 현재 감정 상태")
            emotion = st.session_state.current_emotion
            emotion_color = get_emotion_color(emotion)  # 정에 따른 색상 가져오기
            st.markdown(f"""
            <div style="
                display: flex;
                align-items: center;
                gap: 8px;
                margin-top: 16px;
            ">
                <span style="
                    background-color: {emotion_color};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-weight: 600;
                ">{emotion}</span>
            </div>
            """, unsafe_allow_html=True)
    
            # 대화 통계 표시
            if 'conversation_stats' in st.session_state:
                st.markdown("### 대화 통계")
                stats = st.session_state.conversation_stats
                st.write(f"- 총 대화 수: {stats.get('total', 0)}")
                st.write(f"- 긍정적 감정: {stats.get('positive', 0)}")
                st.write(f"- 부정적 감정: {stats.get('negative', 0)}")
    
            # 음성 파일 업로더
            st.markdown("### 음성 파일 업로드")
            uploaded_audio = st.file_uploader("지원 형식: WAV", type=["wav"])
    
            if uploaded_audio is not None and uploaded_audio != st.session_state.last_uploaded_audio:
                st.session_state.last_uploaded_audio = uploaded_audio
                handle_audio_upload(uploaded_audio)


    # 메인 채팅 영역
    st.title("채팅")
    
    # 채팅 입력 영역을 컬럼으로 분할
    col1, col2 = st.columns([0.1, 0.9])
    
    with col1:
        # 마이크 버튼
        mic_status = "녹음 중..." if st.session_state.get('audio_recorder_state', False) else "음성 녹음"
        if st.button("🎙️", key="mic_button", help=mic_status):
            st.session_state.audio_recorder_state = not st.session_state.get('audio_recorder_state', False)
            
    with col2:
        # 텍스트 입력
        prompt = st.chat_input("메시지를 입력하세요...")

    # 녹음 상태 표시
    if st.session_state.get('audio_recorder_state', False):
        st.markdown("""
            <div class='recording-indicator'>
                녹음 중... 🎙️
            </div>
        """, unsafe_allow_html=True)

    # 음성 녹음 처리
    if st.session_state.get('audio_recorder_state', False):
        try:
            # PyAudio 설정
            CHUNK = 1024
            FORMAT = pyaudio.paFloat32
            CHANNELS = 1
            RATE = 16000

            p = pyaudio.PyAudio()
            stream = p.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK
            )

            # 녹음 중임을 표시
            with st.spinner("녹음 중..."):
                frames = []
                for i in range(0, int(RATE / CHUNK * 5)):  # 5초 녹음
                    data = stream.read(CHUNK)
                    frames.append(data)

            # 녹음 종료 및 정리
            stream.stop_stream()
            stream.close()
            p.terminate()

            # 녹음된 데이터를 WAV 파일로 저장
            with wave.open("temp_recording.wav", 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))

            # 음성을 텍스트로 변환
            with open("temp_recording.wav", "rb") as audio_file:
                audio_text, detected_language = process_audio_input(
                    audio_file.read(),
                    language_options=('ko-KR', 'en-US')
                )

            if audio_text:
                # 텍스트로 변환된 음성을 채팅창에 추가
                chatbot = st.session_state.chatbot_service
                emotions = chatbot.analyze_emotion(audio_text)
                dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
                response = chatbot.get_response(audio_text)

                current_time = datetime.now().strftime('%p %I:%M')
                st.session_state.messages.extend([
                    {
                        "role": "user",
                        "content": f"[음성 메시지] {audio_text}",
                        "emotion": dominant_emotion,
                        "timestamp": current_time
                    },
                    {
                        "role": "assistant",
                        "content": response,
                        "timestamp": current_time
                    }
                ])

                # 통계 업데이트
                update_conversation_stats(dominant_emotion)
                st.rerun()

        except Exception as e:
            st.error(f"음성 녹음 중 오류가 발생했습니다: {str(e)}")
            
        finally:
            st.session_state.audio_recorder_state = False

    # 기존의 텍스트 입력 처리 코드
    if prompt:
        if prompt.strip():
            chatbot = st.session_state.chatbot_service
            emotions = chatbot.analyze_emotion(prompt)
            dominant_emotion = max(emotions.items(), key=lambda x: x[1])[0]
            response = chatbot.get_response(prompt)

            current_time = datetime.now().strftime('%p %I:%M')
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
                "emotion": dominant_emotion,
                "timestamp": current_time
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": response,
                "timestamp": current_time
            })

            # 통계 업데이트
            update_conversation_stats(dominant_emotion)

            st.rerun()


if __name__ == "__main__":
    main()

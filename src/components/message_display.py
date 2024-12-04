import streamlit as st

# def get_emotion_color(emotion: str) -> str:
#     """Return background color based on emotion"""
#     emotion_colors = {
#         # Positive emotions
#         'Happy': 'linear-gradient(135deg, #90EE90, #98FB98)',  # Light green gradient
#         'Neutral': 'linear-gradient(135deg, #FEE500, #FFE44D)',  # Yellow gradient
        
#         # Negative emotions
#         'Sad': 'linear-gradient(135deg, #ADD8E6, #87CEEB)',  # Light blue gradient
#         'Anger': 'linear-gradient(135deg, #FFB6C1, #FFA07A)',  # Light red gradient
#         'Fear': 'linear-gradient(135deg, #DDA0DD, #D8BFD8)',  # Light purple gradient
#         'Disgust': 'linear-gradient(135deg, #F0E68C, #EEE8AA)'  # Light khaki gradient
#     }
#     return emotion_colors.get(emotion, 'linear-gradient(135deg, #FEE500, #FFE44D)')

def get_emotion_color(emotion: str) -> str:
    """Return solid background color based on emotion"""
    emotion_colors = {
        # Positive emotions
        'Happy': '#90EE90',  # Light green
        'Neutral': '#FFD700',  # Gold

        # Negative emotions
        'Sad': '#ADD8E6',  # Light blue
        'Anger': '#FF6347',  # Tomato
        'Fear': '#DDA0DD',  # Plum
        'Disgust': '#F0E68C'  # Khaki
    }
    return emotion_colors.get(emotion, '#FFD700')  # Default to gold for neutral

def display_message(message: dict):
    """Display chat message with emotion-based styling"""
    role = message.get('role', '')
    content = message.get('content', '')
    timestamp = message.get('timestamp', '')
    emotion = message.get('emotion', '')
    
    # Assistant message (left side)
    if role == "assistant":
        st.markdown(f"""
            <div style="display: flex; justify-content: flex-start; margin: 16px 0;">
                <div style="
                    background-color: #F0F0F0;
                    color: black;
                    padding: 12px 18px;
                    border-radius: 18px;
                    border-top-left-radius: 4px;
                    max-width: 80%;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    position: relative;
                ">
                    <div style="font-size: 1rem; line-height: 1.4;">{content}</div>
                    <div style="
                        font-size: 0.75rem;
                        color: #666;
                        margin-top: 6px;
                        text-align: right;
                    ">{timestamp}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    # User message (right side)
    else:
        background = get_emotion_color(emotion)
        st.markdown(f"""
            <div style="display: flex; justify-content: flex-end; margin: 16px 0;">
                <div style="
                    background: {background};
                    color: black;
                    padding: 12px 18px;
                    border-radius: 18px;
                    border-top-right-radius: 4px;
                    max-width: 80%;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    position: relative;
                ">
                    <div style="font-size: 1rem; line-height: 1.4;">{content}</div>
                    <div style="
                        display: flex;
                        justify-content: flex-end;
                        align-items: center;
                        gap: 8px;
                        margin-top: 6px;
                    ">
                        <span style="
                            font-size: 0.75rem;
                            background-color: rgba(0,0,0,0.1);
                            padding: 2px 8px;
                            border-radius: 12px;
                            font-weight: 500;
                        ">{emotion}</span>
                        <span style="font-size: 0.75rem; color: #333;">{timestamp}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# Add custom CSS for chat container
def apply_chat_styles():
    """Apply custom styles for chat interface"""
    st.markdown("""
        <style>
        /* 기본 앱 스타일: 전체 화면 사용 */
        .stApp {
            max-width: 100%;
            margin: 0;
            padding: 0;
        }
        
        /* 메시지 컨테이너 스타일 */
        .element-container {
            margin: 0 !important;
            padding: 0 !important;
        }
        
        .chat-message {
            margin: 0.5rem 0;
        }
        
        .stMarkdown {
            width: 100%;
        }
        
        /* 사용자 메시지 오른쪽 정렬 */
        .st-emotion-cache-janbn0 {
            flex-direction: row-reverse;
            text-align: right;
        }
        
        /* 사용자 메시지 컨테이너 오른쪽 정렬 */
        .st-emotion-cache-janbn0 .st-emotion-cache-1gulkj3 {
            margin-left: auto;
            margin-right: 0;
        }
        
        /* 챗봇 메시지는 왼쪽 정렬 유지 */
        .st-emotion-cache-1uhf5eu {
            flex-direction: row;
            text-align: left;
        }
        
        /* 채팅 입력창 스타일 */
        .stTextInput input {
            background-color: #2D2D2D;
            color: white;
            border: none;
            border-radius: 0.5rem;
            padding: 0.8rem;
        }
        
        /* 버튼 스타일 */
        .stButton button {
            background-color: #007AFF;
            color: white;
            border: none;
            border-radius: 0.5rem;
            padding: 0.8rem 1.5rem;
        }
        
        /* 스크롤바 스타일 */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }
        
        ::-webkit-scrollbar-track {
            background: #1E1E1E;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #4A4A4A;
            border-radius: 4px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #5A5A5A;
        }
        
        /* 마이크 버튼 스타일 */
        .mic-button {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #007AFF;
            color: white;
            border: none;
            cursor: pointer;
            transition: background-color 0.3s;
        }

        .mic-button:hover {
            background-color: #0056b3;
        }

        .mic-button.recording {
            background-color: #dc3545;
            animation: pulse 1.5s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        
        /* 마이크 이미지 버튼 스타일 */
        .stImage {
            cursor: pointer;
            transition: transform 0.3s;
        }
        
        .stImage:hover {
            transform: scale(1.1);
        }
        
        .stImage.recording {
            animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        
        /* 녹음 버튼 스타일 */
        .stButton button {
            width: 40px !important;
            height: 40px !important;
            border-radius: 50% !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 1.5rem !important;
            background-color: #007AFF !important;
            transition: all 0.3s ease !important;
        }
        
        .stButton button:hover {
            background-color: #0056b3 !important;
            transform: scale(1.1) !important;
        }
        
        /* 녹음 중일 때 버튼 스타일 */
        .audio_recorder_state .stButton button {
            background-color: #dc3545 !important;
            animation: pulse 1.5s infinite !important;
        }
        
        /* 녹음 중 표시 스타일 */
        .recording-indicator {
            color: #dc3545;
            font-size: 0.9rem;
            margin-top: 0.5rem;
            text-align: center;
            animation: blink 1s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        
        @keyframes blink {
            0% { opacity: 1; }
            50% { opacity: 0.5; }
            100% { opacity: 1; }
        }
        </style>
    """, unsafe_allow_html=True)
def get_emotion_class(emotion: str) -> str:
    """감정에 따른 스타일 클래스 반환"""
    positive_emotions = {'joy', 'love', 'surprise'}
    negative_emotions = {'anger', 'sadness', 'fear'}
    
    if emotion in positive_emotions:
        return 'positive'
    elif emotion in negative_emotions:
        return 'negative'
    return 'neutral' 

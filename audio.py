import streamlit as st
from audio_recorder_streamlit import audio_recorder
from audiorecorder import audiorecorder
from st_audiorec import st_audiorec
import openai
import base64

#initialize openai client
def setup_openai_client(api_key):
    return openai.OpenAI(api_key= api_key)

#transcribe audio to text
def transcribe_audio(client, audio_path):
    with open(audio_path, 'rb') as audio_file:
        transcript = client.audio.transcriptions.create(model = "whisper-1", file = audio_file)
        return transcript.text
    
#taking response from openai
def fetch_ai_response(client, input_text):
    messages = [{"role":"user","content":input_text}]
    response = client.chat.completions.create(model="gpt-4o-2024-05-13",messages=messages)
    return response.choices[0].message.content

#convert text to audio
def text_to_audio(client, text, audio_path):
    response = client.audio.speech.create(model="tts-1", voice= "nova", input = text)
    response.stream_to_file(audio_path)

def main():
    st.sidebar.title("API KEY CONFIGURATION")
    api_key = st.sidebar.text_input("Enter your OpenAI API key", type="password")

    st.title("Learn Language By Speaking")
    st.write(":microphone: Click on the voice recorder to interact with me. How can I assit you in learning a new language ?")
    # st.session_state.audio_bytes  = audio_recorder(
    #     text="Click on mic to start recording",
    #     pause_threshold=1.0,
    #     key=st.session_state.key_recorder,
    #     )

    if 'messages' not in st.session_state:
        st.session_state['messages'] = []

    recorded_audio = st_audiorec()
    #check if apo key is there
    if api_key:
        client = setup_openai_client(api_key)

        if recorded_audio:
            audio_file = "audio.mp3"
            with open(audio_file, "wb") as f:
                f.write(recorded_audio)
            transcribed_text = transcribe_audio(client, audio_file)
            st.write("Trancribed Text: ",transcribed_text)

            # Update conversation history
            st.session_state['messages'].append({"role": "user", "content": transcribed_text})

            ai_response = fetch_ai_response(client, transcribed_text)
            st.session_state['messages'].append({"role": "assistant", "content": ai_response})


            # ai_response = fetch_ai_response(client, transcribed_text)
            response_audio_file = "ai_response.mp3"
            text_to_audio(client, ai_response, response_audio_file)
            st.audio(response_audio_file)
            st.write("AI Response", ai_response)




if __name__ == "__main__":
    main()


                                     
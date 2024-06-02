import openai
import streamlit as st
import os
from dotenv import load_dotenv
import speech_recognition as sr
import pyttsx3

# Load environment variables from .env file
load_dotenv()

# Set the OpenAI API key
openai_api_key = os.getenv("MY_KEY")

if openai_api_key is None:
    openai_api_key = st.text_input("Enter your OpenAI API Key", type="password")

if openai_api_key == "" or openai_api_key is None or "sk-" not in openai_api_key:
    st.write("#")
    st.warning(
        "⬅️ Please introduce your OpenAI API Key (make sure to have funds) to continue..."
    )
else:
    openai.api_key = openai_api_key

    # Initialize the recognizer and text-to-speech engine
    recognizer = sr.Recognizer()
    tts_engine = pyttsx3.init()

    # Function to get voice answer
    def get_voice_answer(question):
        with sr.Microphone() as source:
            st.write(question)
            tts_engine.say(question)
            tts_engine.runAndWait()
            st.write("Listening...")
            audio = recognizer.listen(source)
            try:
                answer = recognizer.recognize_google(audio)
                st.write(f"You said: {answer}")
            except sr.UnknownValueError:
                answer = "Sorry, I did not understand that."
                st.write(answer)
        return answer

    # Session setup
    def setup_session():
        st.title("Session Setup")
        session = {}
        session['length'] = st.selectbox("Select session length", ["short", "medium", "long"])
        session['type'] = st.selectbox("Select session type", ["Quiz", "Writing", "Voice"])
        session['topic'] = st.text_input("Enter topic of the session")
        session['words_phrases'] = st.text_input("Enter words/phrases to learn (comma-separated)").split(',')
        if st.button("Start Session"):
            st.session_state['session'] = session
            st.session_state['step'] = 'generate_questions'
        return session

    # Generate questions using GPT-4o-2024-05-13
    def generate_questions(session):
        st.title("Generating Questions...")
        prompt = f"Generate {session['length']} {session['type']} questions on the topic '{session['topic']}' focusing on the following words/phrases: {', '.join(session['words_phrases'])}."

        # Create a message object
        message = {
            "role": "user",
            "content": prompt
        }
        response = openai.ChatCompletion.create(
            model="gpt-4o-2024-05-13",
            messages=[message],
            max_tokens=500,
            temperature=0.7
        )

        questions = response.choices[0].message.content.strip().split('\n')
        st.session_state['questions'] = questions
        st.session_state['step'] = 'get_answers'
        st.experimental_rerun()

    # Get answers from the user
    def get_answers(questions, session_type):
        st.title("Answer the Questions")
        answers = []
        if session_type == 'Quiz' or session_type == 'Writing':
            for i, question in enumerate(questions):
                answer = st.text_input(f"{question}", key=f"answer_{i}")
                answers.append(answer)
            if st.button("Submit Answers"):
                st.session_state['answers'] = answers
                st.session_state['step'] = 'evaluate_answers'
                st.experimental_rerun()
        elif session_type == 'Voice':
            for i, question in enumerate(questions):
                answer = get_voice_answer(question)
                answers.append(answer)
            if st.button("Submit Voice Answers"):
                st.session_state['answers'] = answers
                st.session_state['step'] = 'evaluate_answers'
                st.experimental_rerun()
        return answers

    # Evaluate the answers using GPT-4o-2024-05-13
    def evaluate_answers(questions, answers):
        st.title("Evaluating Answers")
        evaluation = []
        for question, answer in zip(questions, answers):
            prompt = f"Evaluate the following answer for correctness. Provide 3 options if the answer is incorrect, else state 'Correct'.\n\nQuestion: {question}\nAnswer: {answer}\n\nEvaluation:"

            # Create a message object
            message = {
                "role": "user",
                "content": prompt
            }
            response = openai.ChatCompletion.create(
                model="gpt-4o-2024-05-13",
                messages=[message],
                max_tokens=150,
                temperature=0.7
            )

            evaluation_response = response.choices[0].message.content.strip()
            if 'Correct' in evaluation_response:
                feedback = "Correct"
                correct = True
            else:
                options = evaluation_response.split('\n')
                if len(options) > 1:
                    correct = False
                    feedback = "Incorrect. Choose the correct answer from the following options:\n" + '\n'.join(options[:3])
                    user_choice = st.selectbox("Select the correct answer", options[:3], key=f"choice_{question}")
                    if st.button("Submit Choice", key=f"submit_{question}"):
                        if user_choice == options[0]:
                            correct = True
                            feedback = "Correct"
                        else:
                            feedback = f"Incorrect. The correct answer is: {options[0]}"
                else:
                    feedback = f"Incorrect. The correct answer is: {options[0]}"
                    correct = False

            evaluation.append({
                'question': question,
                'answer': answer,
                'correct': correct,
                'feedback': feedback
            })

        st.session_state['evaluation'] = evaluation
        st.session_state['step'] = 'show_results'
        st.experimental_rerun()

    # Show the final evaluation results
    def show_results(evaluation):
        st.title("Evaluation Results")
        for result in evaluation:
            st.write(f"Question: {result['question']}")
            st.write(f"Your Answer: {result['answer']}")
            st.write(f"Feedback: {result['feedback']}")
            st.write("---")

    # Main function to run the Streamlit app
    def main():
        if 'step' not in st.session_state:
            st.session_state['step'] = 'setup_session'

        if st.session_state['step'] == 'setup_session':
            setup_session()
        elif st.session_state['step'] == 'generate_questions':
            generate_questions(st.session_state['session'])
        elif st.session_state['step'] == 'get_answers':
            get_answers(st.session_state['questions'], st.session_state['session']['type'])
        elif st.session_state['step'] == 'evaluate_answers':
            evaluate_answers(st.session_state['questions'], st.session_state['answers'])
        elif st.session_state['step'] == 'show_results':
            show_results(st.session_state['evaluation'])

    if __name__ == "__main__":
        main()

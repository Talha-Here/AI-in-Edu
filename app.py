import openai
import streamlit as st
# importing os module for environment variables
import os
# importing necessary functions from dotenv library
from dotenv import load_dotenv, dotenv_values 
# loading variables from .env file
load_dotenv() 

# Function to set and validate the OpenAI API key
# def set_api_key():
#     api_key = st.text_input("Enter your OpenAI API Key", type="password")
#     if api_key:
#         openai.api_key = api_key
#         st.session_state['api_key_set'] = True
openai.api_key = os.getenv("MY_KEY")
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
    response = openai.chat.completions.create(
        model="gpt-4o-2024-05-13",
        messages=[message],
        max_tokens=50,
        temperature=0.7
    )
    
    # questions = response.choices[0].text.strip().split('\n')
    # questions = [choice['message']['content'] for choice in response.choices]
    # completion = response.choices[0]  # Assuming there's always one choice
    # questions = completion.text.strip().split('\n')
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
        st.write("Voice input is not supported in this demo. Please use 'Quiz' or 'Writing' type.")
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
        response = openai.chat.completions.create(
            model="gpt-4o-2024-05-13",
            messages=[message],
            max_tokens=50,
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
    # if 'api_key_set' not in st.session_state:
    #     st.session_state['api_key_set'] = False

    # if not st.session_state['api_key_set']:
    #     set_api_key()
    # else:
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

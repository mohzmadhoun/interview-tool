from openai import OpenAI
import streamlit as st
from streamlit_js_eval import streamlit_js_eval

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# set the page title and icon to chat emoji
st.set_page_config(page_title="Interview Simulator", page_icon="💬")
st.title("Interview Simulator")

# Initialize session state variables
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "user_message_count" not in st.session_state:
    st.session_state.user_message_count = 0
if "feedback_shown" not in st.session_state:
    st.session_state.feedback_shown = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_complete" not in st.session_state:
    st.session_state.chat_complete = False


# Helper functions to update session state
def complete_setup():
    st.session_state.setup_complete = True

def show_feedback():
    st.session_state.feedback_shown = True

def complete_chat():
    st.session_state.chat_complete = True

# Setup stage
if not st.session_state.setup_complete:
    st.subheader("Personal Information", divider = "rainbow")

    # Initialize session state variables for personal information
    if "name" not in st.session_state:
        st.session_state["name"] = "Alex"
    if "experience" not in st.session_state:
        st.session_state["experience"] = "2 years of experience"
    if "skills" not in st.session_state:
        st.session_state["skills"] = "Python, Machine Learning, Data Science"

    st.session_state["name"] = st.text_input(label="Name", value=st.session_state["name"], max_chars=40, placeholder="Enter your name")
    st.session_state["experience"] = st.text_area(label="Experience", value=st.session_state["experience"], height=None, max_chars=200, placeholder="Enter your experience")
    st.session_state["skills"] = st.text_area(label="Skills", value=st.session_state["skills"], height=None, max_chars=200, placeholder="Enter your skills")

    # st.write(f"**Name:** {st.session_state['name']}")
    # st.write(f"**Experience:** {st.session_state['experience']}")
    # st.write(f"**Skills:** {st.session_state['skills']}")

    st.subheader("Company and Position", divider = "rainbow")

    # Initialize session state variables for company and position
    if "level" not in st.session_state:
        st.session_state["level"] = "Junior"
    if "position" not in st.session_state:
        st.session_state["position"] = "Software Engineer"
    if "company" not in st.session_state:
        st.session_state["company"] = "Google"

    col1, col2 = st.columns(2)
    with col1:
        st.session_state["level"] = st.radio(
            label="Choose level",
            key="visibility",
            index=0,
            options=["Junior", "Mid-level", "Senior"],
        )
    with col2:
        st.session_state["position"] = st.selectbox(
            label="Choose a position",
            options=["Software Engineer", "Data Scientist", "Data Engineer", "Machine Learning Engineer", "Full Stack Developer", "Frontend Developer", "Backend Developer", "DevOps Engineer", "Cybersecurity Engineer", "IT Support"],
            index=0,
            placeholder="Select a position",
        )

    st.session_state["company"] = st.selectbox(
        label="Choose a company",
        options=["Google", "Facebook", "Apple", "Microsoft", "Amazon", "Netflix", "Twitter", "Instagram", "Snapchat", "TikTok"],
        index=0,
        placeholder="Select a company",
    )

    # st.write(f"**Your Information:** {st.session_state['level']} {st.session_state['position']} at {st.session_state['company']}")

    if st.button("Start Interview", on_click=complete_setup):
        st.write("Setup complete. Starting interview...")

# Interview stage
if st.session_state.setup_complete and not st.session_state.feedback_shown and not st.session_state.chat_complete:
    st.info(
        """
        Start by introducing yourself.
        """,
        icon = "👋"
    )

    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-5"

    if not st.session_state.messages:
        st.session_state.messages = [
            {
                "role": "system",
                "content": (f"You are an HR executive that interviews an interviewee called {st.session_state['name']} "
                            f"with experience {st.session_state['experience']} and skills {st.session_state['skills']}. "
                            f"You should interview him for the position {st.session_state['level']} {st.session_state['position']} "
                            f"at the company {st.session_state['company']}")
            }
        ]

    for message in st.session_state.messages:
        if message['role'] != 'system':
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if st.session_state.user_message_count < 3:
        if prompt := st.chat_input("Ask a question about your resume", max_chars=1000):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                # with st.spinner("Thinking..."):
                stream = client.chat.completions.create(
                    model=st.session_state.openai_model,
                    messages=[{'role': m['role'], 'content': m['content']} for m in st.session_state.messages],
                    stream=True,
                )
                response = st.write_stream(stream)
            st.session_state.messages.append({"role": "assistant", "content": response})

            st.session_state.user_message_count += 1

    if st.session_state.user_message_count >= 3:
        st.info(
            """
            Thank you for your interview. Here is your feedback:
            """,
            icon = "📝"
        )
        complete_chat()

if st.session_state.chat_complete and not st.session_state.feedback_shown:
    if st.button("Show Feedback", on_click=show_feedback):
        st.write("Fetching feedback...")

if st.session_state.feedback_shown:
    st.subheader("Feedback", divider="rainbow")
    st.write("Here is your feedback:")
    
    conversation_history = "\n".join([f"{message['role']}: {message['content']}" for message in st.session_state.messages])

    feedback_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    feedback_completion = feedback_client.chat.completions.create(
        model=st.session_state.openai_model,
        messages=[
            {
                "role": "system",
                "content": """You are a helpful tool that provides feedback on an interviewee performance.
                                Before the Feedback give a score of 1 to 10.
                                Follow this format:
                                Overal Score: //Your score
                                Feedback: //Here you put your feedback
                                Give only the feedback do not ask any additional questins.
                            """
            },
            {"role": "user", "content": f"This is the interview you need to evaluate. Keep in mind that you are only a tool. And you shouldn't engage in any converstation: {conversation_history}"}
        ],
    )

    st.write(feedback_completion.choices[0].message.content)

    if st.button("Restart the interview", type="primary"):
        streamlit_js_eval(js_expressions="parent.window.location.reload()")
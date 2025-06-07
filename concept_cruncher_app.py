import streamlit as st
from backend.auth import register_user, authenticate_user, get_user_id
from backend.chat import generate_response
from backend.summary import trigger_summary_update
from backend.graph_data_fetching_logic import graph_data
import uuid


# Initialize session state variables
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "selected_subject" not in st.session_state:
    st.session_state.selected_subject = None
if "selected_main_topic" not in st.session_state:
    st.session_state.selected_main_topic = None
if "selected_sub_topic" not in st.session_state:
    st.session_state.selected_sub_topic = None
if "chosen_strategy" not in st.session_state:
    st.session_state.chosen_strategy = ""


# App Title
st.title("Concept Cruncher")

# Tabbed Layout for User Interface
tabs = st.tabs(["Login/Register", "Select Topic", "Chat"])

# ✅ Initialize chat_id
if "chat_id" not in st.session_state:
    st.session_state.chat_id = str(uuid.uuid4())

# ✅ Login/Register Tab
with tabs[0]:
    st.subheader("User Authentication")

    if st.session_state.get("logged_in", False):
        st.success(f"Logged in as {st.session_state.username}")
        
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user_id = None
            st.session_state.chat_id = None
            st.session_state.chat_history = []
            st.success("Logged out successfully.")

    else:
        menu = ["Login", "Register"]
        choice = st.radio("Choose an option:", menu)

        if choice == "Login":
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login"):
                if authenticate_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_id = get_user_id(username)  # or however you get this
                    st.session_state.chat_id = str(uuid.uuid4())
                    st.session_state.chat_history = []
                    st.success(f"Welcome, {username}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")

        elif choice == "Register":
            username = st.text_input("Choose a Username")
            password = st.text_input("Choose a Password", type="password")
            
            if st.button("Register"):
                if register_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_id = get_user_id(username)
                    st.session_state.chat_id = str(uuid.uuid4())
                    st.session_state.chat_history = []
                    st.success(f"Registration successful! Welcome, {username}!")
                else:
                    st.error("Username already exists. Please choose a different one.")


# ✅ Topic Selection Tab
with tabs[1]:
    st.subheader("Select Your Topic")
    if not st.session_state.logged_in:
        st.warning("Please login first.")
    else:
        subject = st.selectbox("Choose a Subject", list(graph_data.keys()), key="subject")
        if subject:
            main_topic = st.selectbox("Choose a Main Topic", list(graph_data[subject].keys()), key="main_topic")
            if main_topic:
                sub_topic = st.selectbox("Choose a Sub-Topic", graph_data[subject][main_topic], key="sub_topic")

                # Store in session state
                st.session_state.selected_subject = subject
                st.session_state.selected_main_topic = main_topic
                st.session_state.selected_sub_topic = sub_topic



# ✅ Chat Interface Tab
with tabs[2]:
    st.subheader("Chat with Concept Cruncher")
    if not st.session_state.logged_in:
        st.warning("Please login first.")
    elif not st.session_state.selected_subject:
        st.warning("Please select a topic first.")
    else:

        # Display chat history
        chat_container = st.container()
        with chat_container:
            for entry in st.session_state.chat_history:
                role = entry["role"]
                message = entry["message"]
                st.markdown(f"**{role.capitalize()}:** {message}")

        # User input and chat
        user_input = st.chat_input("Type your message here...")
        if user_input:
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            st.session_state.chat_history.append({"role": "user", "message": user_input})
            # 💡 CALL TO BACKEND USING THE CLASS-BASED SYSTEM
            bot_response = generate_response(user_input)  # uses ResponseGenerator internally
            
            if bot_response:
                st.session_state.chat_history.append({"role": "bot", "message": bot_response})
            # Only trigger summary update every 6 interactions
            if len(st.session_state.chat_history) % 6 == 0:
                trigger_summary_update()
            # Now rerun
            st.rerun()

        # Add a button to trigger summary update
        if st.button("Summarize Now"):
            trigger_summary_update()


# ✅ User History Sidebar
with st.sidebar:
        #Display current topic context
        st.markdown(f"### Current Topic: {st.session_state.selected_subject} > {st.session_state.selected_main_topic} > {st.session_state.selected_sub_topic}")

        # Display chosen strategy
        if "chosen_strategy" in st.session_state:
            st.info(f"Current Response Strategy: {st.session_state.chosen_strategy}")

# ✅ Debugging



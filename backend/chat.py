# backend/chat.py

from backend.response_generator import ResponseGenerator
import os
import streamlit as st

api_key = os.getenv("OPENAI_API_KEY")
response_generator = ResponseGenerator(api_key)

def generate_response(user_input):
    response, strategy = response_generator.generate_response(
        subject=st.session_state.selected_subject,
        main_topic=st.session_state.selected_main_topic,
        sub_topic=st.session_state.selected_sub_topic,
        chat_history=st.session_state.chat_history,
        user_id=st.session_state.user_id
    )
    st.session_state.chosen_strategy = strategy
    return response












'''




from langchain.chains import LLMChain
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from backend.graph_data_fetching_logic import fetch_node_context
from backend.summary import fetch_most_recent_summary
from backend.graph_data_fetching_logic import get_graph_response
from langchain.chat_models import ChatOpenAI
import uuid 
from langchain.prompts import PromptTemplate
import streamlit as st  
import os

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

### Set up Memory, Prompt Templates, and Responce Chain ###
# ✅ Get Memory Function
# This function returns a memory instance based on the specified type.
# It supports both buffer memory and summary memory, allowing for flexible memory management in the chat application.
# It is used in the get_graph_response function to manage chat history and context.
def get_memory(memory_type="buffer", **kwargs):
    """Get a configurable memory instance."""
    if memory_type == "buffer":
        return ConversationBufferMemory(max_token_limit=10, **kwargs) # kwargs allows for additional parameters like input_key, memory_key, etc.
    elif memory_type == "summary": # Summary memory for long-term context
        llm = ChatOpenAI(openai_api_key=api_key, temperature=0.7, model_name="gpt-3.5-turbo")
        return ConversationSummaryMemory(llm=llm, input_key="chat_history", output_key="summary", **kwargs)
    else:
        raise ValueError(f"Unsupported memory type: {memory_type}")

# ✅ Generate Prompt Template Function
# This function generates a prompt template based on input variables and a template string.
# Used in the choose_response_strategy and get_graph_response functions to create tailored prompts for different response strategies.
def generate_prompt_template(input_variables, template):
    """Generate a dynamic prompt template."""
    return PromptTemplate(input_variables=input_variables, template=template)

# ✅ Create Response Chain Function
# This function creates a response chain using the specified prompt template and memory.
# It initializes a language model chain with the OpenAI API key and specified temperature.
def create_response_chain(prompt_template, memory=None, temperature=0.7):
    """Create a dynamic response chain with a single memory object."""
    llm = ChatOpenAI(openai_api_key=api_key, temperature=temperature, model_name="gpt-3.5-turbo")
    return LLMChain(llm=llm, prompt=prompt_template, memory=memory, output_key="output")


### Chat Response Logic ###
# ✅ Generate AI Response Function: Main Function called by Streamlit. 
# This function generates a response based on the user's input, selected topics, and chat history.
# It uses the get_graph_response and choose_responce_strategy to fetch the node context and user summary, and then generates a response using the chosen strategy.
def generate_response(user_input):
    try:
        response, strategy = get_graph_response(
            subject=st.session_state.selected_subject or "General",
            main_topic=st.session_state.selected_main_topic or "General Topic",
            sub_topic=st.session_state.selected_sub_topic or "General Sub-Topic",
            chat_history=st.session_state.chat_history,
            user_id=st.session_state.user_id
        )
        st.session_state.chat_history.append({"role": "ai", "message": response})
        st.session_state.chosen_strategy = strategy

    except Exception as e:
        error_message = f"⚠️ Error generating response: {str(e)}"
        st.session_state.chat_history.append({"role": "ai", "message": error_message})
        st.error(error_message)

# STEP 1: CHOOSE RESPONSE STRATEGY
# ✅ Choose Response Strategy Function
# This function determines the best response strategy based on the user's input and the context of the topic.
def choose_response_strategy(node_context, user_input):
    """Agent selects the response strategy based on user input and context."""
    prompt_template = generate_prompt_template(
        input_variables=["node_context", "user_input"],
        template="""
        You are an intelligent tutoring agent.
        Based on the student's question and the topic context, choose the best response strategy:
        1. Socratic Method (ask the student more questions).
        2. Lecture Style (explain the concept clearly and in detail).
        3. Quiz Style (ask a few guiding questions and provide feedback).

        Topic Context: "{node_context}"
        Student's Question: "{user_input}"
        What is the best strategy (1, 2, or 3) and why?
        """
    )

    chain = create_response_chain(prompt_template)
    strategy_decision = chain.run({"node_context": node_context, "user_input": user_input})

    if "1" in strategy_decision:
        return "socratic"
    elif "2" in strategy_decision:
        return "lecture"
    elif "3" in strategy_decision:
        return "quiz"
    else:
        return "lecture"  # Default to lecture style

# STEP 2: GET GRAPH RESPONSE based on strategy
# ✅ Get Graph Response Function
# This function generates a response using the graph data, user summary, and chat history.
# Using the selected choice strategy, it creates a tailored response for the user.
# It fetches the node context based on the subject and topics, retrieves the user's summary, and uses buffer memory to manage the chat history.
def get_graph_response(subject, main_topic=None, sub_topic=None, chat_history=None, user_id=None):
    """Generate a response with buffer memory using graph data."""
    node_context = fetch_node_context(subject, main_topic, sub_topic)

    # Fetch the user summary from the database
    user_summary = fetch_most_recent_summary(user_id)
    user_summary_text = "".join(user_summary) if user_summary else "No prior summary available."

    # Use buffer memory for the chain
    memory = get_memory(memory_type="buffer", input_key="node_context", memory_key="chat_history", return_messages=True)

    # Determine the response strategy with context
    user_input = chat_history[-1]['message'] if chat_history else ""
    strategy = choose_response_strategy(node_context, user_input)

# ⚠️ Debugging: 
    # Display the chosen strategy
    print(f"Chosen Strategy: {strategy}")
    print("=== Prompt Inputs ===")
    print("node_context:", node_context)
    print("user_summary_text:", user_summary_text)
    print("user_input:", user_input)

    # Load appropriate prompt based on strategy
    if strategy == "socratic":
        prompt_template = generate_prompt_template(
            input_variables=["node_context", "chat_history", "user_summary", "user_input"],
            template="""You are an AI tutor using the Socratic method. Ask guiding questions to help the student explore the topic.
            Topic Context: {node_context}
            Here is what we know about the student:{user_summary}
            Student's Response: {user_input}"""
        )
    elif strategy == "lecture":
        prompt_template = generate_prompt_template(
            input_variables=["node_context", "chat_history", "user_summary", "user_input"],
            template="""You are an AI tutor giving a clear, step-by-step explanation of the topic.
            Topic Context: {node_context}
            Here is what we know about the student:{user_summary}
            Student's Response: {user_input}"""
        )
    else:  # Quiz
        prompt_template = generate_prompt_template(
            input_variables=["node_context", "chat_history", "user_summary", "user_input"],
            template="""You are an AI tutor quizzing the student. Ask a few questions and provide feedback.
            Topic Context: {node_context}
            Here is what we know about the student:{user_summary}
            Student's Response: {user_input}"""
        )

    # Create the response chain
    chain = create_response_chain(prompt_template, memory=memory)
    response = chain.run({
        "node_context": node_context,
        "chat_history": chat_history,
        "user_summary": user_summary_text,
        "user_input": user_input  # Include the missing user_input key
    })

    # Return both the response and the chosen strategy
    return response, strategy


'''
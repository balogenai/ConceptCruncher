import sqlite3
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationSummaryMemory
from dotenv import load_dotenv
import os
import streamlit as st

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

def save_summary_to_db(user_id, chat_id, summary):
    """Save a summary to the SQLite database."""
    try:
        conn = sqlite3.connect("data/concept_cruncher.db")
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id TEXT NOT NULL,
                summary TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        c.execute("INSERT INTO summaries (user_id, chat_id, summary, timestamp) VALUES (?, ?, ?, datetime('now'))", 
                  (user_id, chat_id, summary))
        conn.commit()
        print(f"Summary saved for user_id: {user_id}, chat_id: {chat_id}, summary: {summary}")
    except Exception as e:
        print(f"Error saving summary to DB: {e}")
    finally:
        conn.close()

def fetch_summaries_from_db(user_id):
    """Fetch summaries for a user from the SQLite database."""
    conn = sqlite3.connect("data/concept_cruncher.db")
    c = conn.cursor()
    c.execute("SELECT summary FROM summaries WHERE user_id = ?", (user_id,))
    summaries = [row[0] for row in c.fetchall()]
    conn.close()
    return summaries

def fetch_most_recent_summary(user_id):
    """Fetch the most recent summary for a user from the SQLite database."""
    conn = sqlite3.connect("data/concept_cruncher.db")
    c = conn.cursor()
    c.execute("SELECT summary FROM summaries WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def update_user_summary(user_id, chat_id, chat_history):
    print(f"Updating summary for user_id: {user_id}, chat_id: {chat_id}")
    
    llm = ChatOpenAI(openai_api_key=api_key, temperature=0.7, model_name="gpt-3.5-turbo")
    summary_memory = ConversationSummaryMemory(
        llm=llm,
        max_token_limit=800  # Adjust as needed
    )

    try:
        # 1. Fetch most recent summary from DB
        combined_past_summary = fetch_most_recent_summary(user_id)

        # 2. Feed combined past summary into memory
        if combined_past_summary:
            summary_memory.chat_memory.add_user_message("Summary of previous sessions:")
            summary_memory.chat_memory.add_ai_message(combined_past_summary)

        # 3. Process current chat history
        for i in range(0, len(chat_history) - 1, 2):
            user_msg = chat_history[i]
            bot_msg = chat_history[i + 1] if i + 1 < len(chat_history) else None

            if user_msg["role"] == "user" and bot_msg and bot_msg["role"] in ["bot", "ai"]:
                inputs = {"input": user_msg["message"]}
                outputs = {"output": bot_msg["message"]}
                summary_memory.save_context(inputs, outputs)

        # 4. Combine all into a new summary
        summary_raw = "".join(
            [msg.content if hasattr(msg, "content") else str(msg) for msg in summary_memory.buffer]
        )
        new_summary = f"Summary of user interactions and prior sessions: {summary_raw}"

        # 5. Save to DB
        save_summary_to_db(user_id, chat_id, new_summary)
        print(f"Summary updated for user_id: {user_id}, chat_id: {chat_id}")

    except Exception as e:
        print(f"Error updating summary: {e}")



def trigger_summary_update():
    """Safely trigger a summary update, ensuring all session state variables are set."""

    # Initialize user_id and chat_id if not present
    if 'user_id' not in st.session_state or 'chat_id' not in st.session_state:
        print("Error: user_id or chat_id is not set in session state.")
        return

    # Validate chat history
    if not isinstance(st.session_state['chat_history'], list):
        print("Error: chat_history must be a list.")
        return

    try:
        update_user_summary(
            st.session_state['user_id'],
            st.session_state['chat_id'],
            st.session_state['chat_history']
        )
        print("Summary updated successfully.")

    except Exception as e:
        print(f"Error updating summary: {e}")

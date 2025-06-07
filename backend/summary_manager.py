# backend/summary_manager.py
### NOT USED ###
import sqlite3
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationSummaryMemory
import os
from dotenv import load_dotenv

load_dotenv()

class SummaryManager:
    def __init__(self, db_path="data/concept_cruncher.db", api_key=None):
        self.db_path = db_path
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.llm = ChatOpenAI(openai_api_key=self.api_key, temperature=0.7, model_name="gpt-3.5-turbo")

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def save_summary(self, user_id, chat_id, summary):
        try:
            conn = self._connect()
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
        except Exception as e:
            print(f"Error saving summary to DB: {e}")
        finally:
            conn.close()

    def fetch_all_summaries(self, user_id):
        conn = self._connect()
        c = conn.cursor()
        c.execute("SELECT summary FROM summaries WHERE user_id = ?", (user_id,))
        summaries = [row[0] for row in c.fetchall()]
        conn.close()
        return summaries

    def fetch_latest_summary(self, user_id):
        conn = self._connect()
        c = conn.cursor()
        c.execute("SELECT summary FROM summaries WHERE user_id = ? ORDER BY timestamp DESC LIMIT 1", (user_id,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def update_summary(self, user_id, chat_id, chat_history):
        print(f"Updating summary for user_id: {user_id}, chat_id: {chat_id}")
        summary_memory = ConversationSummaryMemory(llm=self.llm, max_token_limit=300)

        try:
            past = self.fetch_all_summaries(user_id)
            combined_past = " ".join(past)

            if combined_past:
                summary_memory.chat_memory.add_user_message("Summary of previous sessions:")
                summary_memory.chat_memory.add_ai_message(combined_past)

            for i in range(0, len(chat_history) - 1, 2):
                user_msg = chat_history[i]
                bot_msg = chat_history[i + 1] if i + 1 < len(chat_history) else None

                if user_msg["role"] == "user" and bot_msg and bot_msg["role"] in ["bot", "ai"]:
                    summary_memory.save_context(
                        {"input": user_msg["message"]},
                        {"output": bot_msg["message"]}
                    )

            summary_text = "".join([msg.content for msg in summary_memory.buffer if hasattr(msg, "content")])
            full_summary = f"Summary of user interactions and prior sessions: {summary_text}"
            self.save_summary(user_id, chat_id, full_summary)
            print(f"Summary updated for user_id: {user_id}, chat_id: {chat_id}")

        except Exception as e:
            print(f"Error updating summary: {e}")

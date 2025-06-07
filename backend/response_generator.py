from langchain.chains import LLMChain
from dotenv import load_dotenv
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from backend.graph_data_fetching_logic import fetch_node_context
from backend.summary import fetch_most_recent_summary
from backend.prompt_templates import get_strategy_prompt, get_response_prompt
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

class ResponseGenerator:
    def __init__(self, api_key, model_name="gpt-3.5-turbo", temperature=0.7):
        self.api_key = api_key
        self.temperature = temperature
        self.model_name = model_name
        self.llm = ChatOpenAI(openai_api_key=self.api_key, temperature=self.temperature, model_name=self.model_name)

    def get_memory(self, memory_type="buffer", **kwargs):
        if memory_type == "buffer":
            return ConversationBufferMemory(max_token_limit=10, **kwargs)
        elif memory_type == "summary":
            return ConversationSummaryMemory(llm=self.llm, input_key="chat_history", output_key="summary", **kwargs)
        else:
            raise ValueError(f"Unsupported memory type: {memory_type}")

    def generate_prompt_template(self, input_variables, template):
        return PromptTemplate(input_variables=input_variables, template=template)

    def create_chain(self, prompt_template, memory=None):
        return LLMChain(llm=self.llm, prompt=prompt_template, memory=memory, output_key="output")

    def choose_strategy(self, node_context, user_input):
        template = get_strategy_prompt()
        prompt_template = self.generate_prompt_template(["node_context", "user_input"], template)
        chain = self.create_chain(prompt_template)
        strategy_decision = chain.run({"node_context": node_context, "user_input": user_input})

        if "1" in strategy_decision:
            return "socratic"
        elif "2" in strategy_decision:
            return "lecture"
        elif "3" in strategy_decision:
            return "quiz"
        return "lecture"  # default fallback

    def generate_response(self, subject, main_topic, sub_topic, chat_history, user_id):
        node_context = fetch_node_context(subject, main_topic, sub_topic)
        user_summary = fetch_most_recent_summary(user_id) or ["No prior summary available."]
        user_input = chat_history[-1]['message'] if chat_history else ""

        strategy = self.choose_strategy(node_context, user_input)

        memory = self.get_memory(
            memory_type="buffer",
            input_key="node_context",
            memory_key="chat_history",
            return_messages=True
        )
        prompt_str = get_response_prompt(strategy)
        prompt_template = self.generate_prompt_template(
            ["node_context", "chat_history", "user_summary", "user_input"],
            prompt_str
        )

        chain = self.create_chain(prompt_template, memory=memory)
        response = chain.run({
            "node_context": node_context,
            "chat_history": chat_history,
            "user_summary": "".join(user_summary),
            "user_input": user_input
        })

        return response, strategy

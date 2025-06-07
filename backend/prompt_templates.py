# backend/prompt_templates.py

def get_strategy_prompt():
    return """
    You are an intelligent tutoring agent.
    Based on the student's question and the topic context, choose the best response strategy:
    1. Socratic Method (ask the student more questions).
    2. Lecture Style (explain the concept clearly and in detail).
    3. Quiz Style (ask a few guiding questions and provide feedback).

    Topic Context: "{node_context}"
    Student's Question: "{user_input}"
    What is the best strategy (1, 2, or 3) and why?
    """

def get_response_prompt(strategy):
    if strategy == "socratic":
        return """You are an AI tutor using the Socratic method...
        Topic Context: {node_context}
        Student's Response: {user_input}
        Student Summary: {user_summary}
        """
    elif strategy == "lecture":
        return """You are an AI tutor giving a clear, step-by-step explanation...
        Topic Context: {node_context}
        Student's Response: {user_input}
        Student Summary: {user_summary}
        """
    elif strategy == "quiz":
        return """You are an AI tutor quizzing the student...
        Topic Context: {node_context}
        Student's Response: {user_input}
        Student Summary: {user_summary}
        """
    else:
        raise ValueError("Unknown strategy")

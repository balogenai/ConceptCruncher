#### TOPIC GRAPH DATA ####
graph_data = {
    "Algebra": {
        "Factoring Polynomials": [
            "Factoring Quadratics",
            "Factoring by Grouping",
            "Factoring Special Products"
        ]
    },
    "Math": {
        "Arithmetic with Fractions": [
            "Adding Fractions",
            "Subtracting Fractions",
            "Multiplying Fractions",
            "Dividing Fractions"
        ]
    },
    "Chemistry": {
        "Periodic Trends": [
            "Atomic Radius",
            "Ionization Energy",
            "Electronegativity"
        ]
    }
}

def fetch_node_context(subject, main_topic=None, sub_topic=None):
    """Fetch context for a specific node in the graph."""
    if subject not in graph_data:
        return "Subject not found."

    if main_topic:
        if main_topic not in graph_data[subject]:
            return "Main topic not found."

        if sub_topic:
            if sub_topic in graph_data[subject][main_topic]:
                return f"{subject} > {main_topic} > {sub_topic}"
            else:
                return "Sub-topic not found."

        return f"{subject} > {main_topic}"

    return f"{subject}"

def get_graph_response(subject, main_topic=None, sub_topic=None, chat_history=None, user_id=None):
    """Generate a response with buffer memory using graph data."""
    node_context = fetch_node_context(subject, main_topic, sub_topic)

    # Use buffer memory for the chain
    memory = get_memory(memory_type="buffer", input_key="node_context", memory_key="chat_history", return_messages=True)

    # Determine the response strategy with context
    user_input = chat_history[-1]['message'] if chat_history else ""
    strategy = choose_response_strategy(node_context, user_input)

    # Display the chosen strategy
    print(f"Chosen Strategy: {strategy}")

    # Load appropriate prompt based on strategy
    if strategy == "socratic":
        prompt_template = generate_prompt_template(
            input_variables=["node_context", "chat_history"],
            template="You are an AI tutor using the Socratic method. Ask guiding questions to help the student explore the topic.")
    elif strategy == "lecture":
        prompt_template = generate_prompt_template(
            input_variables=["node_context", "chat_history"],
            template="You are an AI tutor giving a clear, step-by-step explanation of the topic.")
    else:  # Quiz
        prompt_template = generate_prompt_template(
            input_variables=["node_context", "chat_history"],
            template="You are an AI tutor quizzing the student. Ask a few questions and provide feedback.")

    # Create the response chain
    chain = create_response_chain(prompt_template, memory=memory)
    response = chain.run({"node_context": node_context, "chat_history": chat_history})

    # Update the summary every 6 messages
    if len(chat_history) % 6 == 0:
        update_user_summary(user_id, chat_history)

    # Return both the response and the chosen strategy
    return response, strategy

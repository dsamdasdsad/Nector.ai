import streamlit as st

# ----------------------------------------------------------------------
# AP CSP CORE ALGORITHM: run_pipeline
# (This is the function you will screenshot for Written Responses 3b, 3c, 3d)
# ----------------------------------------------------------------------

def call_together_ai(api_key, model_name, prompt, temperature, max_tokens):
    """Call Together.ai API and return the model's response."""
    import requests

    url = "https://api.together.xyz/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": int(max_tokens)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return f"Error: Status {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"


def clean_response(text):
    """Remove <think> blocks that some models return."""
    import re
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    cleaned = cleaned.strip()
    return cleaned if cleaned else text


def run_pipeline(start_text, step_list, model_list):
    """
    Takes input and runs it through a sequence of AI prompts.
    Parameters:
        start_text (str): The user's initial input.
        step_list (list): List of dictionaries with 'model' and 'prompt' keys.
        model_list (list): List of registered model dictionaries.
    Returns:
        list: A list of cleaned response strings, one per step.
    """
    current_text = start_text
    all_results = []

    # ITERATION: Process each step in the workflow
    for step_info in step_list:
        # SELECTION: Find the matching model in the registry
        chosen_model = None
        for m in model_list:
            if m['name'] == step_info['model']:
                chosen_model = m
                break

        # SELECTION: Error handling if model not found
        if chosen_model is None:
            all_results.append(f"Error: Model '{step_info['model']}' not found.")
            return all_results

        # SEQUENCING: Build the full prompt and call the API
        full_prompt = step_info['prompt'] + "\n\nInput: " + current_text
        raw_output = call_together_ai(
            chosen_model['api_key'],
            chosen_model['endpoint'],
            full_prompt,
            chosen_model['temperature'],
            chosen_model['max_tokens']
        )

        # Data cleaning
        clean_output = clean_response(raw_output)

        # Store result and prepare for next iteration
        all_results.append(clean_output)
        current_text = clean_output

    return all_results


# ----------------------------------------------------------------------
# STREAMLIT UI (Everything below is the interface for the video)
# ----------------------------------------------------------------------

st.set_page_config(page_title="Nector AI", page_icon="🔗", layout="wide")

# Session state initialization
if 'models' not in st.session_state:
    st.session_state.models = []
if 'workflows' not in st.session_state:
    st.session_state.workflows = []

st.title("🔗 Nector AI")
st.markdown("### Connect and orchestrate AI models")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Choose a page:", ["Dashboard", "Models", "Workflows"])

# -------------------- DASHBOARD --------------------
if page == "Dashboard":
    st.header("📊 Dashboard")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Registered Models", len(st.session_state.models))
    with col2:
        st.metric("Created Workflows", len(st.session_state.workflows))
    with col3:
        st.metric("Status", "Ready")

    st.subheader("Quick Start")
    st.markdown("""
    1. Go to **Models** page to register your AI models
    2. Go to **Workflows** page to create your first workflow
    3. Run your workflow and see the results!
    """)

# -------------------- MODELS PAGE --------------------
elif page == "Models":
    st.header("🤖 AI Models")

    # Display existing models
    if st.session_state.models:
        st.subheader("Registered Models")
        for i, model in enumerate(st.session_state.models):
            with st.expander(f"{model['name']} ({model['type']})"):
                st.write(f"**Type:** {model['type']}")
                st.write(f"**Endpoint:** {model.get('endpoint', 'Default')}")
                if st.button(f"Delete {model['name']}", key=f"delete_{i}"):
                    st.session_state.models.pop(i)
                    st.rerun()

    # Add new model form
    st.subheader("Add New Model")
    with st.form("add_model"):
        model_name = st.text_input("Model Name", placeholder="e.g., My GPT-4")
        model_type = st.selectbox(
            "Model Type",
            ["OpenAI", "Together Ai", "Local (Ollama)", "Custom API"]
        )
        api_endpoint = st.text_input(
            "API Endpoint",
            placeholder="e.g., mistralai/Mistral-7B-Instruct-v0.1",
            help="Use a serverless model identifier from Together.ai"
        )
        api_key = st.text_input("API Key", type="password", help="Your API key will be stored securely")
        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider("Temperature", 0.0, 2.0, 0.7)
        with col2:
            max_tokens = st.number_input("Max Tokens", 100, 4000, 1000)

        submitted = st.form_submit_button("Add Model")
        if submitted and model_name and api_key:
            new_model = {
                'name': model_name,
                'type': model_type,
                'endpoint': api_endpoint,
                'api_key': api_key,
                'temperature': temperature,
                'max_tokens': max_tokens
            }
            st.session_state.models.append(new_model)
            st.success(f"✅ Model '{model_name}' added successfully!")
            st.rerun()
        elif submitted:
            st.error("Please fill in Model Name and API Key")

    # Test model section
    if st.session_state.models:
        st.divider()
        st.subheader("Test Your Model")
        model_selectbox = st.selectbox(
            "Select a model to test",
            options=[model['name'] for model in st.session_state.models]
        )
        model_textinput = st.text_input("Test Prompt", placeholder="e.g., Say hello!")

        if st.button("Test Connection"):
            if model_textinput:
                selected_model = None
                for model in st.session_state.models:
                    if model['name'] == model_selectbox:
                        selected_model = model
                        break
                with st.spinner("Connecting to AI..."):
                    test_response = call_together_ai(
                        api_key=selected_model['api_key'],
                        model_name=selected_model['endpoint'],
                        prompt=model_textinput,
                        temperature=selected_model['temperature'],
                        max_tokens=selected_model['max_tokens']
                    )
                if test_response.startswith("Error:"):
                    st.error(f"❌ {test_response}")
                else:
                    cleaned_response = clean_response(test_response)
                    st.success("✅ Connection successful!")
                    st.info(f"📝 Response from {model_selectbox}:")
                    st.write(cleaned_response)
            else:
                st.error("Please enter a test prompt")

# -------------------- WORKFLOWS PAGE --------------------
elif page == "Workflows":
    st.header("⚙️ Workflows")

    if not st.session_state.models:
        st.warning("⚠️ Please add some models first in the Models page!")
        st.stop()

    # Display existing workflows
    if st.session_state.workflows:
        st.subheader("Existing Workflows")
        for i, workflow in enumerate(st.session_state.workflows):
            with st.expander(f"📄 {workflow['name']}"):
                st.write(f"**Steps:** {len(workflow['steps'])}")
                for j, step in enumerate(workflow['steps']):
                    st.write(f"Step {j+1}: {step['model']}")

                workflow_input = st.text_input(
                    "Enter input text for workflow:",
                    placeholder="Type something to process...",
                    key=f"workflow_input_{i}"
                )

                if st.button(f"Run {workflow['name']}", key=f"run_{i}"):
                    if workflow_input:
                        st.subheader(f"Running: {workflow['name']}")
                        # ********** CALL TO run_pipeline **********
                        output_list = run_pipeline(
                            workflow_input,
                            workflow['steps'],
                            st.session_state.models
                        )
                        # ******************************************
                        for step_num, result_text in enumerate(output_list, 1):
                            st.write(f"**Step {step_num}**")
                            st.write(result_text)
                            st.divider()
                    else:
                        st.warning("⚠️ Please enter input text first")

                if st.button(f"Delete {workflow['name']}", key=f"delete_workflow_{i}"):
                    st.session_state.workflows.pop(i)
                    st.rerun()

    # Create new workflow form
    st.subheader("Create New Workflow")
    with st.form("create_workflow"):
        workflow_name = st.text_input("Workflow Name", placeholder="e.g., Text Analysis Pipeline")
        num_steps = st.number_input("Number of Steps", 1, 5, 2)

        steps = []
        for i in range(num_steps):
            st.write(f"**Step {i+1}:**")
            col1, col2 = st.columns(2)
            with col1:
                selected_model = st.selectbox(
                    f"Select Model for Step {i+1}",
                    options=[model['name'] for model in st.session_state.models],
                    key=f"model_step_{i}"
                )
            with col2:
                step_prompt = st.text_area(
                    f"Prompt Template for Step {i+1}",
                    placeholder="Enter your prompt here...",
                    key=f"prompt_step_{i}",
                    height=100
                )
            steps.append({'model': selected_model, 'prompt': step_prompt})

        submitted = st.form_submit_button("Create Workflow")
        if submitted and workflow_name:
            new_workflow = {'name': workflow_name, 'steps': steps}
            st.session_state.workflows.append(new_workflow)
            st.success(f"✅ Workflow '{workflow_name}' created successfully!")
            st.rerun()
        elif submitted:
            st.error("Please enter a workflow name")

st.sidebar.markdown("---")
st.sidebar.markdown("**Nector AI v1.0**")
st.sidebar.markdown("Made with Streamlit")
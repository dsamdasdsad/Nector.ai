from logging import PlaceHolder
from unittest import result
import streamlit as st
import json
import os
import time

# Configure the page
st.set_page_config(
    page_title="Nector AI",
    page_icon="🔗",
    layout="wide"
)

# Initialize session state for storing data
if 'models' not in st.session_state:
    st.session_state.models = []

if 'workflows' not in st.session_state:
    st.session_state.workflows = []

# Main title
st.title("🔗 Nector AI")
st.markdown("### Connect and orchestrate AI models")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    ["Dashboard", "Models", "Workflows"]
)

# Dashboard Page
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

# Models Page
elif page == "Models":
    st.header("🤖 AI Models")
    
    # Show existing models
    if st.session_state.models:
        st.subheader("Registered Models")
        for i, model in enumerate(st.session_state.models):
            with st.expander(f"{model['name']} ({model['type']})"):
                st.write(f"**Type:** {model['type']}")
                st.write(f"**Endpoint:** {model.get('endpoint', 'Default')}")
                if st.button(f"Delete {model['name']}", key=f"delete_{i}"):
                    st.session_state.models.pop(i)
                    st.experimental_rerun()
    
    # Add new model form
    st.subheader("Add New Model")
    
    with st.form("add_model"):
        model_name = st.text_input("Model Name", placeholder="e.g., My GPT-4")
        
        model_type = st.selectbox(
            "Model Type",
            ["OpenAI", "Anthropic", "Local (Ollama)", "Custom API"]
        )
        
        api_endpoint = st.text_input(
            "API Endpoint", 
            placeholder="e.g., https://api.openai.com/v1/chat/completions"
        )
        
        api_key = st.text_input(
            "API Key", 
            type="password",
            help="Your API key will be stored securely"
        )
        
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
            st.experimental_rerun()
        elif submitted:
            st.error("Please fill in Model Name and API Key")

    if st.session_state.models:
        st.divider()    
        st.subheader("Test Your Model")
        
        model_selectbox = st.selectbox(
            "Select a model to test",
            options=[model['name'] for model in st.session_state.models]
        )

        model_textinput = st.text_input(
            "Test Prompt",
            placeholder="e.g., Say hello!"
        )

        if st.button("Test Connection"):
            if model_textinput:   # type: ignore
                with st.spinner("Loading... Please wait."):
                    time.sleep(3)  # 3-second delay  
                test_response = f"I'm {model_selectbox} and I received: {model_textinput}. This is a demo"
                st.success("Demo success")
                st.info(f"📝 Response: {test_response}")

            else:
                st.error("Please enter a test prompt")

# Workflows Page
elif page == "Workflows":
    st.header("⚙️ Workflows")
    
    if not st.session_state.models:
        st.warning("⚠️ Please add some models first in the Models page!")
        st.stop()
    
    # Show existing workflows
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
                        
                        progress_bar = st.progress(0)
                        
                        current_workflow = st.session_state.workflows[i]
                        total_steps = len(current_workflow['steps'])
                        
                        results = []
                        previous_output = workflow_input
                        
                        for step_num, step in enumerate(current_workflow['steps'], 1):
                            
                            st.info(f"⚙️ Step {step_num}: {step['model']}")
                            
                            progress_bar.progress(step_num / total_steps)
                            
                            time.sleep(1.5)
                            
                            fake_output = f"Demo output from {step['model']} (Step {step_num}). Processed: '{previous_output}'"
                            
                            results.append({
                                'step': step_num,
                                'model': step['model'],
                                'output': fake_output
                            })
                            
                            st.success(f"✅ Step {step_num} complete!")

                            previous_output = fake_output
                        
                        st.success("🎉 Workflow completed! (Demo Mode)")
                        
                        with st.expander("📊 View Detailed Results"):
                            for result in results:
                                st.write(f"**Step {result['step']} - {result['model']}**")
                                st.write(result['output'])
                                st.divider()
                    
                    else:
                        st.warning("⚠️ Please enter input text first")
                
                if st.button(f"Delete {workflow['name']}", key=f"delete_workflow_{i}"):
                    st.session_state.workflows.pop(i)
                    st.experimental_rerun()
    
    # Create new workflow
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
            
            steps.append({
                'model': selected_model,
                'prompt': step_prompt
            })
        
        submitted = st.form_submit_button("Create Workflow")
        
        if submitted and workflow_name:
            new_workflow = {
                'name': workflow_name,
                'steps': steps
            }
            st.session_state.workflows.append(new_workflow)
            st.success(f"✅ Workflow '{workflow_name}' created successfully!")
            st.experimental_rerun()
        elif submitted:
            st.error("Please enter a workflow name")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Nector AI v1.0**")
st.sidebar.markdown("Made with ❤️ and Streamlit")
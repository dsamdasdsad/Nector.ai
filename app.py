from logging import PlaceHolder
from unittest import result
import streamlit as st
import json
import os
import time

#Defining the function so it would be called later on without any bugs
def call_together_ai(api_key, model_name, prompt, temperature, max_tokens):
    """Call Together.ai API"""
    import requests
    
    url = "https://api.together.xyz/v1/chat/completions" #URL of together ai, all api requests will be coming from here
    
    #identity pass
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    #Sets the parameters of the ai
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": int(max_tokens)
    }
    
    #sends out api requests and try catch errors
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return f"Error: Status {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

#removes the think block of think models
def clean_response(text):
    """Remove think blocks from AI responses"""
    import re
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Remove extra whitespace
    cleaned = cleaned.strip()
    return cleaned if cleaned else text

#basic page settings
st.set_page_config(
    page_title="Nector AI",
    page_icon="🔗",
    layout="wide"
)

#Start the models list if doesn't, also preserves data
if 'models' not in st.session_state:
    st.session_state.models = []

#Start the workflows list if doesn't, also preserves data
if 'workflows' not in st.session_state:
    st.session_state.workflows = []

#basic introduction on the app
st.title("🔗 Nector AI")
st.markdown("### Connect and orchestrate AI models")

#sidebar's title
st.sidebar.title("Navigation")
page = st.sidebar.selectbox(
    "Choose a page:",
    ["Dashboard", "Models", "Workflows"]
)

#creates 3 important values to view 
if page == "Dashboard":
    st.header("📊 Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Registered Models", len(st.session_state.models))
    
    with col2:
        st.metric("Created Workflows", len(st.session_state.workflows))
    
    with col3:
        st.metric("Status", "Ready")
    
    #creates an introduction the app itself
    st.subheader("Quick Start")
    st.markdown("""
    1. Go to **Models** page to register your AI models
    2. Go to **Workflows** page to create your first workflow
    3. Run your workflow and see the results!
    """)

#code for the models page
elif page == "Models":
    st.header("AI Models")
    # checking if models in contain any true values
    if st.session_state.models:
        #if yes, then the program lets the user choose its models, api endpoint (model pathway), user api key 
        st.subheader("Registered Models")
        for i, model in enumerate(st.session_state.models):
            with st.expander(f"{model['name']} ({model['type']})"):
                st.write(f"**Type:** {model['type']}")
                st.write(f"**Endpoint:** {model.get('endpoint', 'Default')}")
                if st.button(f"Delete {model['name']}", key=f"delete_{i}"):
                    st.session_state.models.pop(i)
                    st.rerun()

    st.subheader("Add New Model")
    
    #the button add finalizes all the prior inputs and save 
    with st.form("add_model"):
        model_name = st.text_input("Model Name", placeholder="e.g., My GPT-4")
        
        model_type = st.selectbox(
            "Model Type",
            ["OpenAI", "Together Ai", "Local (Ollama)", "Custom API"]
        )
        
        api_endpoint = st.text_input(
            "API Endpoint", 
            placeholder="e.g., meta-llama/Llama-2-7b-chat-hf", help="Together.ai model identifier (find in their model catalog)"
        )
        
        api_key = st.text_input(
            "API Key", 
            type="password",
            help="Your API key will be stored securely"
        )
        
        #2 major change-able parameters 
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

    #testing section
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

        
        #runs the connection between the website and the ai endpoint
        if st.button("Test Connection"):
            if model_textinput:
                
                selected_model = None
                for model in st.session_state.models:
                    if model['name'] == model_selectbox:
                        selected_model = model
                        break
                
                #calls the parameters listed below, utilizes the text input from earlier as prompt
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
                    #utilizes the cleaned response
                    cleaned_response = clean_response(test_response)  
                    st.success("✅ Connection successful!")
                    st.info(f"📝 Response from {model_selectbox}:")
                    st.write(cleaned_response)  
            else:
                st.error("Please enter a test prompt")
            
    

        
#workflow page
elif page == "Workflows":
    st.header("⚙️ Workflows")
    
    #error for no models
    if not st.session_state.models:
        st.warning("⚠️ Please add some models first in the Models page!")
        st.stop()
    
    if st.session_state.workflows:
        #existing workflows section
        st.subheader("Existing Workflows")
        #numbering workflows
        for i, workflow in enumerate(st.session_state.workflows):
            with st.expander(f"📄 {workflow['name']}"):
                st.write(f"**Steps:** {len(workflow['steps'])}")
                #relating steps with the amount of models
                for j, step in enumerate(workflow['steps']):
                    st.write(f"Step {j+1}: {step['model']}")
                
                #workflow's input
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
                            
                            if workflow_input:
                                selected_workflow = None
                                for model in st.session_state.models:
                                    if model['name'] == step['model']:
                                        selected_workflow = model
                                        break
                            else:
                                st.error("Please enter a test prompt")
                            
                            # Check if model found
                            if selected_workflow is None:
                                st.error(f"Cannot find model: {step['model']}")
                                break

                            #combines the prompts
                            full_prompt = f"{step['prompt']}\n\nInput: {previous_output}"

                            # Call real API
                            with st.spinner(f"Running {step['model']}..."):
                                real_output = call_together_ai(
                                    api_key=selected_workflow['api_key'],
                                    model_name=selected_workflow['endpoint'],
                                    prompt=full_prompt,
                                    temperature=selected_workflow['temperature'],
                                    max_tokens=selected_workflow['max_tokens']
                                )

                            # Check for errors
                            if real_output.startswith("Error:"):
                                st.error(f"Malfunctioning model: {step['model']}")
                                break
                            
                            cleaned_output = clean_response(real_output) 

                            results.append({
                                'step': step_num,
                                'model': step['model'],
                                'output': cleaned_output  
                            })
                            
                            st.success(f"✅ Step {step_num} complete!")

                            previous_output = cleaned_output
                        
                        st.success("Workflow completed!")
                        
                        st.divider()
                        #results page 
                        st.write("**Results:**")
                        for result in results:
                            st.write(f"**Step {result['step']} - {result['model']}**")
                            st.write(result['output'])
                            st.divider()
                    
                    else:
                        st.warning("⚠️ Please enter input text first")
                
                #deletes the workflow
                if st.button(f"Delete {workflow['name']}", key=f"delete_workflow_{i}"):
                    st.session_state.workflows.pop(i)
                    st.rerun()
    
    st.subheader("Create New Workflow")
    
    with st.form("create_workflow"):
        #functions that relate with creating a new workflow
        workflow_name = st.text_input("Workflow Name", placeholder="e.g., Text Analysis Pipeline")
        
        num_steps = st.number_input("Number of Steps", 1, 5, 2)
        
        steps = []
        for i in range(num_steps):
            st.write(f"**Step {i+1}:**")
            
            col1, col2 = st.columns(2)
            
            #chooses the first model
            with col1:
                selected_model = st.selectbox(
                    f"Select Model for Step {i+1}",
                    options=[model['name'] for model in st.session_state.models],
                    key=f"model_step_{i}"
                )
            
            #chooses the secont model and so on
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
        
        #creates a new workflow
        if submitted and workflow_name:
            new_workflow = {
                'name': workflow_name,
                'steps': steps
            }
            st.session_state.workflows.append(new_workflow)
            st.success(f"✅ Workflow '{workflow_name}' created successfully!")
            st.rerun()
        elif submitted:
            st.error("Please enter a workflow name")

st.sidebar.markdown("---")
st.sidebar.markdown("**Nector AI v1.0**")
st.sidebar.markdown("Made with Streamlit")
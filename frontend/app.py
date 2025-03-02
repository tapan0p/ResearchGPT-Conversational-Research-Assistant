import streamlit as st
import requests
import json
import re

# Backend API URL
API_BASE_URL = "https://academic-research-paper-assistant.onrender.com"

st.set_page_config(page_title="Academic Research Paper Assistant", layout="wide")

st.title("📚 Welcome! Academic Research Paper Assistant")

# Sidebar Navigation
st.sidebar.header("Navigation")
option = st.sidebar.radio("Go to", ["Home", "Search Papers", "Q&A", "Future Works"])

# Initialize session state for storing papers and selections
if "papers" not in st.session_state:
    st.session_state.papers = []
if "selected_papers" not in st.session_state:
    st.session_state.selected_papers = {}

# Function to clean LLM response - removes thinking part
def clean_llm_response(text):
    # Remove the <think>...</think> section if present
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    cleaned_text = cleaned_text.strip()
    return cleaned_text

# Home Page
if option == "Home":
    st.header("")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("This tool helps you:")
        
        st.markdown("""
        <div style="font-size: 16px; margin-bottom: 10px;">
            <p><span style="font-size: 24px;">🔍</span> Find relevant academic papers</p>
            <p><span style="font-size: 24px;">📊</span> Analyze research trends</p>
            <p><span style="font-size: 24px;">📝</span> Access paper summaries</p>
            <p><span style="font-size: 24px;">📥</span> Download full papers</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("How to use this tool:")
        
        st.markdown("""
        <div style="font-size: 16px;">
            <p><span style="font-size: 18px;">1️⃣</span> Navigate to <strong>Search Papers</strong> to find research on your topic</p>
            <p><span style="font-size: 18px;">2️⃣</span> Select papers of interest for further analysis</p>
            <p><span style="font-size: 18px;">3️⃣</span> Use the <strong>Q&A</strong> section to ask specific questions about selected papers</p>
            <p><span style="font-size: 18px;">4️⃣</span> Explore potential <strong>Future Works</strong> based on the selected papers</p>
        </div>
        """, unsafe_allow_html=True)
    

elif option == "Search Papers":
    st.header("🔍 Search for Research Papers")
    topic = st.text_input("Enter research topic:")
    max_results = st.slider("Number of results", 1, 50, 10)
    years_back = st.slider("Look back years", 1, 20, 5)
    fetch_content = st.checkbox("Fetch paper content", value=True)

    if st.button("Search"):
        with st.spinner("Searching for papers..."):
            response = requests.post(f"{API_BASE_URL}/search", json={
                "topic": topic,
                "max_results": max_results,
                "years_back": years_back,
                "fetch_content": fetch_content
            })

            if response.status_code == 200:
                st.session_state.papers = response.json().get("papers", [])
            else:
                st.error("Failed to fetch papers. Try again.")

    
    for paper in st.session_state.papers:
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(paper.get("title", "Unknown Title"))
                st.write(f"**Authors:** {', '.join(paper.get('authors', []))}")
                st.write(f"**Abstract:** {paper.get('abstract', 'No abstract available')}")
                st.write(f"**Year:** {paper.get('year', 'Unknown Year')}")
                if paper.get("url"):
                    st.markdown(f"[Read More]({paper['url']})")
            with col2:
                paper_id = paper["paper_id"]
                select_paper = st.checkbox("Select for Q&A & Future Work", key=f"select_{paper_id}",
                                           value=st.session_state.selected_papers.get(paper_id, False))
                
                if select_paper:
                    st.session_state.selected_papers[paper_id] = paper.get("title", "Unknown Title")
                else:
                    st.session_state.selected_papers.pop(paper_id, None)
                    

elif option == "Q&A":
    st.header("💬 Ask a Question About Papers")
    question = st.text_area("Enter your question:")

    selected_paper_ids = list(st.session_state.selected_papers.keys())
    
    if not selected_paper_ids:
        st.warning("⚠ No papers selected! Please select papers from the Search page first.")
    else:
        st.write("**Selected Papers:**")
        for paper_id, paper_title in st.session_state.selected_papers.items():
            st.markdown(f"""
            <div style="background-color:#e8f0fe;padding:15px;border-radius:15px;margin-bottom:15px">
                        <h5>📄 <strong style="color: black;">{paper_title}</strong></h5>
                        
            </div>
            """, unsafe_allow_html=True)

        if st.button("Get Answer"):
            with st.spinner("Fetching answer..."):
                response = requests.post(f"{API_BASE_URL}/qa", json={
                    "question": question,
                    "paper_ids": selected_paper_ids
                })

                if response.status_code == 200:
                    # Extract the answer from the response
                    response_data = response.json()
                    answer = response_data.get("answer", "No answer found")
                    
                    # If answer is a dictionary or contains JSON, extract just the text content
                    if isinstance(answer, dict) and "answer" in answer:
                        answer_text = answer.get("answer")
                    elif isinstance(answer, str):
                        # Try to parse as JSON in case it's a JSON string
                        try:
                            parsed = json.loads(answer)
                            if isinstance(parsed, dict) and "answer" in parsed:
                                answer_text = parsed.get("answer")
                            else:
                                answer_text = answer
                        except json.JSONDecodeError:
                            # Not valid JSON, use as it is
                            answer_text = answer
                    else:
                        answer_text = str(answer)
                    
                    # Clean the response to remove thinking part
                    answer_text = clean_llm_response(answer_text)
                    
                    # Display the answer
                    st.markdown(f"""
                    <div style="background-color:#e8f0fe;padding:15px;border-radius:10px;margin-top:10px">
                        <h4 style="color:#333">🤖 Answer:</h4>
                        <div style="color:black;font-size:16px;line-height:1.6">
                            {answer_text}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Failed to fetch answer. Try again.")

elif option == "Future Works":
    st.header("🔮 Generate Future Research Directions")
    topic = st.text_input("Enter research topic:")

    selected_paper_ids = list(st.session_state.selected_papers.keys())

    if not selected_paper_ids:
        st.warning("⚠ No papers selected! Please select papers from the Search page first.")
    else:
        st.write("📄 **Selected Papers:**")
        for paper_id, paper_title in st.session_state.selected_papers.items():
            st.markdown(f"""
            <div style="background-color:#e8f0fe;padding:15px;border-radius:15px;margin-bottom:15px">
                        <h5>📄 <strong style="color: black;">{paper_title}</strong></h5>
                        
            </div>
            """, unsafe_allow_html=True)

        if st.button("Generate"):
            with st.spinner("Generating future research directions..."):
                response = requests.post(f"{API_BASE_URL}/generate-future-works", json={
                    "topic": topic,
                    "paper_ids": selected_paper_ids
                })

                if response.status_code == 200:
                    response_data = response.json()
                    future_work = response_data.get("future_work", "No suggestions available")
                    
                    # Handle case where future_work might be in JSON format
                    if isinstance(future_work, dict):
                        if "future_work" in future_work:
                            future_work = future_work.get("future_work")
                        else:
                            future_work = json.dumps(future_work, indent=2)
                    
                    # Try to parse as JSON in case it's a JSON string
                    try:
                        parsed = json.loads(future_work)
                        if isinstance(parsed, dict) and "future_work" in parsed:
                            future_work = parsed.get("future_work")
                    except (json.JSONDecodeError, TypeError):
                        # Not valid JSON or not a string, use as is
                        pass
                    
                    # Clean the response to remove thinking part
                    answer_text = clean_llm_response(future_work)

                    st.markdown(f"""
                    <div style="background-color:#e8f0fe;padding:15px;border-radius:10px;margin-top:10px">
                        <h4 style="color:#333">🤖 Suggested Future Research:</h4>
                        <div style="color:black;font-size:16px;line-height:1.6">
                            {future_work}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Failed to generate future works. Try again.")


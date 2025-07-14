import streamlit as st
import requests
from bs4 import BeautifulSoup
import openai
import os

# --- Environment Configuration ---
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

client = openai.AzureOpenAI(
    api_key=AZURE_OPENAI_KEY,
    api_version=AZURE_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

# --- Streamlit UI ---
st.title("📊 Company Research Agent (Hiring Lens)")
company = st.text_input("Enter company name", "")
location = st.text_input("Enter location/country (e.g., USA, India, or 'all')", "all")
search_scope = st.radio("Search Scope", ["Search in one country", "Search globally"])

if st.button("Run Research") and company:
    if search_scope == "Search globally" or location.lower() == "all":
        search_query = f"{company} workforce trends and business expansion news"
    else:
        search_query = f"{company} workforce trends and business expansion news in {location}"

    st.info(f"Searching for: {search_query}")

    # --- SerpAPI Search ---
    def search_serpapi(query, num_results=5):
        url = "https://serpapi.com/search.json"
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_API_KEY,
            "num": num_results
        }
        response = requests.get(url, params=params)
        results = response.json().get("organic_results", [])
        return [r.get("link") for r in results[:num_results] if r.get("link")]

    search_links = search_serpapi(search_query)
    st.subheader("🔗 Top Links Found")
    for link in search_links:
        st.markdown(f"- {link}")

    # --- Fetch and Summarize ---
    def fetch_text(url):
        try:
            r = requests.get(url, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            paragraphs = [p.text for p in soup.find_all('p')]
            return '\n'.join(paragraphs[:20])
        except Exception:
            return ""

    def summarize_text(text, company):
        prompt = f"""
        Summarize the following article content with a focus on:
        1. Workforce trends of {company}
        2. Business lines, deals, or restructuring
        3. Any hiring signals or relevance for staffing services

        Content:
        {text[:4000]}
        """
        response = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        return response.choices[0].message.content

    st.subheader("📄 Summary")
    for link in search_links:
        with st.spinner(f"Summarizing: {link}"):
            text = fetch_text(link)
            if text:
                summary = summarize_text(text, company)
                st.markdown(f"**Summary from:** {link}")
                st.write(summary)
                st.markdown("---")

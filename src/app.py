import os
import sys
import re
import streamlit as st 
from qdrant_client import QdrantClient
from embedding import GoogleTextEmbedder
from config.setting import Settings
from utils.data_clean import clean_full
from jinja2 import environment,FileSystemLoader
from langchain_groq import ChatGroq


from dotenv import load_dotenv
load_dotenv()


settings = Settings()


qdrant = QdrantClient(settings.QDRANT_ENDPOINT,
                      api_key=settings.QDRANT_API_KEY,)

st.title('News Search Engine And Summarizer')

st.write('This is a real-time RAG system that allows you to search for news articles and get summaries.')


def get_prompt(filename: str) -> str:
    '''
    Load the prompt template from the given file path.
    '''
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # This is /app/src
    PROMPT_DIR = os.path.join(BASE_DIR, "prompts")         # This is /app/src/prompts
    env  = environment.Environment(loader=FileSystemLoader(PROMPT_DIR))
    Template = env.get_template(filename)
    return Template


def query_vectordatabase(query: str):
    '''
    Search for news articles in the Qdrant database using the query.
    '''

    embedder  = GoogleTextEmbedder()
    embed_query = embedder(query)
    results = qdrant.query_points(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query=embed_query,
        limit=8,
        with_payload=True
    )

    
    return [
        {   'content': clean_full(res.payload['content']),
            "score": res.score,
            "title": res.payload["title"],
            "image": res.payload["image_url"],
            "date": res.payload["published_at"],
            "original": res.payload["url"],
            "source_num" : i + 1
        }
        for i, res in enumerate(results.points)
    ]
    

def generate_summary(query: str) -> str:
    '''
    Generate a summary of the news articles using the query.
    '''


    content = query_vectordatabase(query)
    print(content)
    docu = [{"content":doc['content'],"source_num" : doc['source_num']} for doc in content]
    prompt_template = get_prompt('summary_prompt.j2')
    prompt = prompt_template.render(query=query, documents=docu)

    llm = ChatGroq(model=settings.GROQ_MODEL_ID,api_key=settings.GROQ_API_KEY, temperature=0.1)
    message = [
        ("system",prompt),
        ("human", query)
    ]

    for chunk in llm.stream(message):
        if chunk.content:
            yield chunk.content,content

    

def link_citations(text,source_map):
    '''Replace inline citations in the text with clickable links.
    '''
    def repl(match):
        num = match.group(1)
        url = source_map.get(int(num), "#")
        return f'<a href="{url}" target="_blank">[{num}]</a>'
    return re.sub(r'\[(\d+)\]', repl, text)

def extract_used_citations(text: str) -> set:
    return set(map(int, re.findall(r'\[(\d+)\]', text)))



query = st.text_input("Ask something about current news")

if query:
    response_stream = generate_summary(query)

    final_output = ""
    source_links = {}

    with st.spinner("Generating answer..."):
        for chunk, sources in response_stream:
            final_output += chunk
            source_links = {doc["source_num"]: [doc["original"],doc['title']] for doc in sources}

    st.subheader("🧠 Answer")
    st.markdown(link_citations(final_output, source_links), unsafe_allow_html=True)



    st.subheader("🔗 Sources")
    used_citations = extract_used_citations(final_output)
    # Filter the sources accordingly
    filtered_sources = {
        num: ls for num, ls in source_links.items() if num in used_citations
        }
    for num, ls in filtered_sources.items():
        st.markdown(f"[{num}]: [{ls[1]}]({ls[0]})", unsafe_allow_html=True)



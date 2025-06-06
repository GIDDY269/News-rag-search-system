import os
import sys
import streamlit as st 
from qdrant_client import QdrantClient
from embedding import TextEmbedder
from config.setting import Settings
from utils.data_clean import clean_full
from langchain_core.output_parsers import JsonOutputParser
from jinja2 import environment,FileSystemLoader
from typing import List, Dict, Any,Optional
from langchain_groq import ChatGroq
import requests
from io import BytesIO
from PIL import Image

from dotenv import load_dotenv
load_dotenv()


settings = Settings()


qdrant = QdrantClient(settings.QDRANT_ENDPOINT,
                      api_key=settings.QDRANT_API_KEY,)

st.title('News Search Engine AND SUMMARIZER')

st.write('This is a real-time RAG system that allows you to search for news articles and get summaries.')


def get_prompt(filename: str) -> str:
    '''
    Load the prompt template from the given file path.
    '''
    env  = environment.Environment(loader=FileSystemLoader('src\prompts'))
    Template = env.get_template(filename)
    return Template


def query_vectordatabase(query: str):
    '''
    Search for news articles in the Qdrant database using the query.
    '''

    embedder  = TextEmbedder()
    embed_query = embedder(query,to_list=True)
    results = qdrant.query_points(
        collection_name=settings.QDRANT_COLLECTION_NAME,
        query=embed_query,
        limit=3,
        with_payload=True
    )

    


    return [
        {   'content': clean_full(res.payload['content']),
            "score": res.score,
            "title": res.payload["title"],
            "image": res.payload["image_url"],
            "date": res.payload["published_at"],
            "original": res.payload["url"],
        }
        for res in results.points
    ]
    

def generate_summary(query: str) -> str:
    '''
    Generate a summary of the news articles using the query.
    '''


    content = query_vectordatabase(query)
    print(content)
    docu = [doc['content'] for doc in content]
    prompt_template = get_prompt('summary_prompt.j2')
    prompt = prompt_template.render(query=query, documents=docu)

    llm = ChatGroq(model=settings.GROQ_MODEL_ID,api_key=settings.GROQ_API_KEY, temperature=0.1)
    message = [
        ("system",prompt),
        ("human", query)
    ]

    return llm.invoke(message).content



results_placeholder = st.empty()


def download_and_resize_image(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            resized_img = img.resize((200, 300))
            return resized_img
        else:
            st.error("Failed to download image.")
    except Exception as e:
        st.error(f"Error downloading image: {e}")




def display_articles(articles):
    if articles:
        results_placeholder.empty()
        n_cols = 2
        n_rows = (len(articles) + n_cols - 1) // n_cols
        for row in range(n_rows):
            cols = st.columns(n_cols)
            for col in range(n_cols):
                index = row * n_cols + col
                if index >= len(articles):
                    break
                article = articles[index]
                image = download_and_resize_image(article["image"])
                with cols[col]:
                    if image:
                        st.image(image, use_container_width=True, clamp=True, width=50)
                    st.caption(
                        f"Score: {(100 * article['score']):.2f}% : {article['date']} "
                    )
                    st.subheader(article["title"])
                    url = article["original"]
                    button_html = f"""<a href="{url}" target="_blank">
                                        <button style="color: white; background-color: #4CAF50; border: none; padding: 10px 24px; 
                                        text-align: center; text-decoration: none; display: inline-block; font-size: 16px; 
                                        margin: 4px 2px; cursor: pointer; border-radius: 12px;">
                                            See More
                                        </button>
                                    </a>"""
                    st.markdown(button_html, unsafe_allow_html=True)
            st.divider()







def on_text_enter():
    question = st.session_state.question
    question = clean_full(question)
    if question:
        articles = query_vectordatabase(question)
        if articles:
            st.session_state.question = question
            results_placeholder.write(f"Found {len(articles)} articles for your query.")
            summary = generate_summary(question)
            st.write("Summary:")
            st.write(summary)
        else:
            results_placeholder.write("No articles found for your query.")
        display_articles(articles)


question = st.text_input("What's new?:", key="question", on_change=on_text_enter)













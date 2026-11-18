"""Local Streamlit UI for testing the catalog assistant without Docker."""

import asyncio

import streamlit as st

from app.core.settings import Settings
from app.services.ai_graph import AIWorkflow
from app.services.catalog import ProductRetriever
from app.services.guardrails import validate_message


st.set_page_config(
    page_title="ShopMate AI",
    page_icon="🛒",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {max-width: 1050px; padding-top: 2rem;}
    [data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,.22);}
    .hero {
        padding: 1.4rem 1.6rem; border-radius: 18px; margin-bottom: 1.3rem;
        color: white; background: linear-gradient(125deg, #4f46e5, #7c3aed 55%, #db2777);
        box-shadow: 0 12px 30px rgba(79,70,229,.22);
    }
    .hero h1 {margin: 0 0 .25rem; font-size: 2rem;}
    .hero p {margin: 0; opacity: .9;}
    .source-card {
        padding: .8rem 1rem; margin: .45rem 0; border-radius: 12px;
        border: 1px solid rgba(128,128,128,.25); background: rgba(128,128,128,.07);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def build_workflow(openai_key: str, groq_key: str, model: str, result_count: int) -> tuple[Settings, AIWorkflow]:
    """Create the existing application workflow without DB or Redis services."""
    cfg = Settings(
        environment="development",
        auth_mode="dev",
        retrieval_mode="demo",
        demo_catalog_path="data/products.csv",
        openai_api_key=openai_key,
        groq_api_key=groq_key,
        openai_model=model,
        retrieval_k=result_count,
    )
    return cfg, AIWorkflow(cfg, ProductRetriever(cfg))


async def ask_assistant(workflow: AIWorkflow, question: str, history: list[dict]):
    return await workflow.run(question, history)


with st.sidebar:
    st.header("Test settings")
    st.caption("Keys stay in this browser session and are not written to a file.")
    openai_key = st.text_input("OpenAI API key (optional)", type="password")
    groq_key = st.text_input("Groq API key (optional)", type="password")
    model = st.text_input("OpenAI model", value="gpt-4o-mini")
    result_count = st.slider("Catalog results", 1, 8, 4)

    if openai_key:
        st.success("OpenAI answer generation enabled")
    elif groq_key:
        st.success("Groq answer generation enabled")
    else:
        st.info("Demo mode: catalog matching works without an API key.")

    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.markdown(
    """
    <div class="hero">
      <h1>🛒 ShopMate AI</h1>
      <p>Ask questions about products, prices, ratings, and customer reviews.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.caption("Try: Which phone has a good battery? · Show highly rated products · Suggest a useful kitchen product")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander(f"View {len(message['sources'])} catalog sources"):
                for index, source in enumerate(message["sources"], 1):
                    st.markdown(
                        f"""<div class="source-card"><b>[{index}] {source['product_title']}</b><br>
                        Price: {source.get('price') or 'Not listed'} &nbsp;·&nbsp;
                        Rating: {source.get('rating') or 'Not listed'}<br>
                        <small>Product ID: {source['product_id']}</small></div>""",
                        unsafe_allow_html=True,
                    )

question = st.chat_input("Ask about a product...")
if question:
    try:
        cfg, workflow = build_workflow(openai_key, groq_key, model, result_count)
        clean_question = validate_message(question, cfg.max_input_chars)
        history = [
            {"role": item["role"], "content": item["content"]}
            for item in st.session_state.messages
        ]

        st.session_state.messages.append({"role": "user", "content": clean_question})
        with st.chat_message("user"):
            st.markdown(clean_question)

        with st.chat_message("assistant"):
            with st.spinner("Searching the catalog..."):
                answer, sources = asyncio.run(ask_assistant(workflow, clean_question, history))
            st.markdown(answer)
            source_data = [source.model_dump() for source in sources]
            if source_data:
                with st.expander(f"View {len(source_data)} catalog sources"):
                    for index, source in enumerate(source_data, 1):
                        st.markdown(
                            f"**[{index}] {source['product_title']}**  \n"
                            f"Price: {source.get('price') or 'Not listed'} · "
                            f"Rating: {source.get('rating') or 'Not listed'} · "
                            f"ID: `{source['product_id']}`"
                        )

        st.session_state.messages.append(
            {"role": "assistant", "content": answer, "sources": source_data}
        )
    except Exception as exc:
        st.error(f"The request could not be completed: {exc}")
        st.caption("Check the API key/model, or remove the key to use offline demo mode.")

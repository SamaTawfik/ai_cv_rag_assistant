
import requests
import streamlit as st


st.set_page_config(
    page_title="AI & Computer Vision Assistant",
    page_icon="📚",
    layout="wide",
)

st.title("AI & Computer Vision Knowledge Assistant")
st.caption(
    "Ask questions about your documents and inspect the supporting sources."
)

with st.sidebar:
    st.header("Settings")

    api_url = st.text_input(
        "Backend URL",
        value="http://127.0.0.1:8000",
    ).rstrip("/")

    st.divider()
    st.subheader("Document Upload")

    uploaded_file = st.file_uploader(
        "Choose a PDF document",
        type=["pdf"],
    )

    upload_clicked = st.button(
        "Upload and index",
        disabled=uploaded_file is None,
        use_container_width=True,
    )

    if upload_clicked and uploaded_file is not None:
        try:
            with st.spinner("Uploading and indexing the PDF..."):
                response = requests.post(
                    f"{api_url}/upload",
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf",
                        )
                    },
                    timeout=300,
                )

            if response.ok:
                result = response.json()
                st.success("Document processed successfully.")
                st.json(result)
            else:
                try:
                    detail = response.json().get(
                        "detail", response.text
                    )
                except ValueError:
                    detail = response.text

                st.error(
                    f"Upload failed ({response.status_code}): {detail}"
                )

        except requests.RequestException as exc:
            st.error(f"Could not reach the backend: {exc}")

    st.divider()

    if st.button("Check backend health", use_container_width=True):
        try:
            response = requests.get(
                f"{api_url}/health",
                timeout=10,
            )
            response.raise_for_status()
            st.success("Backend is reachable.")
            st.json(response.json())
        except requests.RequestException as exc:
            st.error(f"Backend health check failed: {exc}")


if "messages" not in st.session_state:
    st.session_state.messages = []


def render_sources(sources):
    if not sources:
        st.caption("No supporting sources were returned.")
        return

    with st.expander(f"Sources ({len(sources)})"):
        for index, source in enumerate(sources, start=1):
            file_name = source.get("file_name", "Unknown file")
            page_number = source.get("page_number")
            excerpt = source.get("excerpt", "")

            if page_number is not None:
                st.markdown(
                    f"**{index}. {file_name} — Page {page_number}**"
                )
            else:
                st.markdown(f"**{index}. {file_name}**")

            if excerpt:
                st.write(excerpt)


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            render_sources(message.get("sources", []))


if question := st.chat_input(
    "Ask a question about AI or Computer Vision..."
):
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    try:
        with st.spinner("Searching documents and generating an answer..."):
            response = requests.post(
                f"{api_url}/ask",
                json={"question": question},
                timeout=180,
            )

        if response.ok:
            result = response.json()

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": result["answer"],
                    "sources": result.get("sources", []),
                }
            )
        else:
            try:
                detail = response.json().get(
                    "detail", response.text
                )
            except ValueError:
                detail = response.text

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": (
                        f"Request failed ({response.status_code}): "
                        f"{detail}"
                    ),
                    "sources": [],
                }
            )

    except requests.RequestException as exc:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": f"Could not connect to the backend: {exc}",
                "sources": [],
            }
        )

    st.rerun()

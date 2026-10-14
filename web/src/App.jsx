
import { useState } from "react";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const SUGGESTIONS = [
  {
    title: "Understand a concept",
    question: "What is object detection?",
    icon: "✳",
  },
  {
    title: "Explore deep learning",
    question: "Explain the main concepts in this document.",
    icon: "⌘",
  },
  {
    title: "Summarize a document",
    question: "Summarize the key points in this document.",
    icon: "≡",
  },
];

export default function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  async function askQuestion(event) {
    event.preventDefault();

    const text = question.trim();
    if (!text || loading) return;

    setMessages((previous) => [
      ...previous,
      { role: "user", content: text },
    ]);

    setQuestion("");
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to get an answer."
        );
      }

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources || [],
        },
      ]);
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setLoading(false);
    }
  }

  async function uploadPDF(event) {
    const file = event.target.files?.[0];
    event.target.value = "";

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please select a PDF file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setUploading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "PDF upload failed."
        );
      }

      setMessages((previous) => [
        ...previous,
        {
          role: "system",
          content: `Indexed ${data.file_name}: ${data.chunks_stored} chunks stored.`,
        },
      ]);
    } catch (err) {
      setError(err.message || "Could not upload the PDF.");
    } finally {
      setUploading(false);
    }
  }

  function chooseSuggestion(text) {
    setQuestion(text);
    setError("");
  }

  return (
    <main className="page">
      <header className="topbar">
        <div className="brand-mark" aria-hidden="true">
          VM
        </div>

        <div className="brand-copy">
          <h1>VisionMind</h1>
          <p>AI & Computer Vision Knowledge Assistant</p>
        </div>

        <span className="status">
          <span className="status-indicator" />
          RAG Assistant
        </span>
      </header>

      <section className="workspace">
        <aside className="sidebar">
          <p className="eyebrow">KNOWLEDGE BASE</p>

          <h2>Your AI library</h2>

          <p className="muted">
            Upload your documents and explore their contents
            through AI-powered questions and answers.
          </p>

          <div className="upload-zone">
            <div className="upload-icon" aria-hidden="true">
              {uploading ? "⋯" : "↑"}
            </div>

            <h3>
              {uploading ? "Processing document" : "Add a document"}
            </h3>

            <p className="upload-description">
              {uploading
                ? "Uploading and indexing your PDF..."
                : "Choose a PDF to add it to your knowledge base."}
            </p>

            <label className="upload-button">
              {uploading ? "Please wait..." : "+ Upload PDF"}
              <input
                type="file"
                accept=".pdf,application/pdf"
                onChange={uploadPDF}
                disabled={uploading}
                hidden
              />
            </label>

            <p className="file-hint">PDF documents only</p>
          </div>

          <div className="note">
            <div className="note-heading">
              <span aria-hidden="true">✦</span>
              <strong>How it works</strong>
            </div>

            <p>
              Your document is divided into smaller text chunks.
              Relevant sections are retrieved for each question
              and used to generate a grounded answer.
            </p>
          </div>

          <div className="privacy-note">
            <span aria-hidden="true">ⓘ</span>
            <p>
              Answers depend on the documents available to
              your assistant.
            </p>
          </div>
        </aside>

        <section className="chat-panel">
          <div className="chat-heading">
            <div>
              <p className="eyebrow">YOUR RESEARCH ASSISTANT</p>
              <h2>Ask your documents</h2>
              <p className="chat-subtitle">
                Find information without searching page by page.
              </p>
            </div>

            <span className="online-dot">
              Ready
            </span>
          </div>

          <div className="conversation" aria-live="polite">
            {messages.length === 0 && (
              <div className="welcome">
                <div className="welcome-icon" aria-hidden="true">
                  ✦
                </div>

                <p className="welcome-eyebrow">
                  YOUR KNOWLEDGE, SIMPLIFIED
                </p>

                <h2>
                  What would you like
                  <br />
                  to discover?
                </h2>

                <p>
                  Ask questions about your uploaded documents.
                  Your assistant will search the available context
                  and help you find the answers.
                </p>

                <div className="suggestions">
                  {SUGGESTIONS.map((item) => (
                    <button
                      key={item.title}
                      type="button"
                      className="suggestion-card"
                      onClick={() => chooseSuggestion(item.question)}
                    >
                      <span
                        className="suggestion-icon"
                        aria-hidden="true"
                      >
                        {item.icon}
                      </span>

                      <span className="suggestion-copy">
                        <strong>{item.title}</strong>
                        <span>{item.question}</span>
                      </span>

                      <span
                        className="suggestion-arrow"
                        aria-hidden="true"
                      >
                        ↗
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((message, index) => (
              <article
                key={`${message.role}-${index}`}
                className={`message ${message.role}`}
              >
                <div className="message-label">
                  {message.role === "user"
                    ? "YOU"
                    : message.role === "system"
                    ? "DOCUMENT STATUS"
                    : "VISIONMIND"}
                </div>

                <p>{message.content}</p>

                {message.sources?.length > 0 && (
                  <details className="sources">
                    <summary>
                      View sources ({message.sources.length})
                    </summary>

                    {message.sources.map((source, sourceIndex) => (
                      <div
                        className="source-card"
                        key={`${source.file_name}-${source.page_number}-${sourceIndex}`}
                      >
                        <strong>
                          {source.file_name}
                          {source.page_number != null
                            ? ` · Page ${source.page_number}`
                            : ""}
                        </strong>

                        <p>{source.excerpt}</p>
                      </div>
                    ))}
                  </details>
                )}
              </article>
            ))}

            {loading && (
              <div className="loading-bubble" role="status">
                <span className="loading-avatar">VM</span>

                <div>
                  <strong>VisionMind is thinking</strong>
                  <p>Searching your documents...</p>

                  <div className="typing-indicator" aria-hidden="true">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              </div>
            )}
          </div>

          {error && (
            <div className="error" role="alert">
              <span aria-hidden="true">!</span>
              <p>{error}</p>
              <button
                type="button"
                onClick={() => setError("")}
                aria-label="Dismiss error"
              >
                ×
              </button>
            </div>
          )}

          <form className="composer" onSubmit={askQuestion}>
            <input
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              placeholder="Ask a question about your documents..."
              disabled={loading}
              aria-label="Your question"
            />

            <button
              type="submit"
              disabled={loading || !question.trim()}
            >
              {loading ? "..." : "Ask ↗"}
            </button>
          </form>

          <p className="disclaimer">
            AI-generated answers may be inaccurate. Verify important
            information against the cited sources.
          </p>
        </section>
      </section>
    </main>
  );
}

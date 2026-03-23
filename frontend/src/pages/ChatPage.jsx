import { useState, useRef, useEffect } from "react";
import api from "../api/client";
import ChatMessage from "../components/ChatMessage";

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [meetings, setMeetings] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [selectedScope, setSelectedScope] = useState([]);
  const [showScope, setShowScope] = useState(false);
  const [allowWebSearch, setAllowWebSearch] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const fetchSources = async () => {
      try {
        const [meetRes, docRes] = await Promise.all([
          api.get("/meetings"),
          api.get("/documents"),
        ]);
        setMeetings(meetRes.data.filter((m) => m.report_validated));
        setDocuments(docRes.data);
      } catch {
        // ignore
      }
    };
    fetchSources();
  }, []);

  const toggleScope = (id) => {
    setSelectedScope((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const question = input.trim();
    if (!question) return;

    const userMsg = { role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const payload = { question, allow_web_search: allowWebSearch };
      if (selectedScope.length > 0) {
        payload.scope = selectedScope;
      }
      const res = await api.post("/chat/ask", payload);
      const assistantMsg = {
        role: "assistant",
        content: res.data.answer,
        sources: res.data.sources,
        usedExternal: res.data.used_external,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg = {
        role: "assistant",
        content: "Erreur : " + (err.response?.data?.detail || err.message),
        sources: [],
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)]">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-2xl font-bold">Chat RAG</h1>
        <button
          onClick={() => setShowScope(!showScope)}
          className={`text-sm px-3 py-1 rounded ${
            selectedScope.length > 0
              ? "bg-blue-100 text-blue-700"
              : "bg-gray-200 text-gray-600"
          }`}
        >
          Filtrer les sources{selectedScope.length > 0 ? ` (${selectedScope.length})` : ""}
        </button>
      </div>

      {showScope && (
        <div className="border rounded-lg p-4 mb-4 max-h-48 overflow-y-auto bg-gray-50">
          <p className="text-xs font-semibold text-gray-500 mb-2">
            Restreindre la recherche à :
          </p>
          {meetings.length === 0 && documents.length === 0 && (
            <p className="text-sm text-gray-400">Aucune source disponible.</p>
          )}
          {meetings.length > 0 && (
            <div className="mb-2">
              <p className="text-xs text-gray-400 mb-1">Comptes-rendus validés</p>
              {meetings.map((m) => (
                <label key={m.id} className="flex items-center gap-2 text-sm py-0.5">
                  <input
                    type="checkbox"
                    checked={selectedScope.includes(m.id)}
                    onChange={() => toggleScope(m.id)}
                  />
                  {m.title}
                </label>
              ))}
            </div>
          )}
          {documents.length > 0 && (
            <div>
              <p className="text-xs text-gray-400 mb-1">Documents</p>
              {documents.map((d) => (
                <label key={d.id} className="flex items-center gap-2 text-sm py-0.5">
                  <input
                    type="checkbox"
                    checked={selectedScope.includes(d.id)}
                    onChange={() => toggleScope(d.id)}
                  />
                  {d.filename}
                </label>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="flex-1 overflow-y-auto space-y-4 pb-4">
        {messages.length === 0 && (
          <p className="text-gray-400 text-center py-12">
            Posez une question sur vos comptes-rendus et documents.
          </p>
        )}
        {messages.map((msg, i) => (
          <ChatMessage key={i} message={msg} />
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-3 text-gray-500 animate-pulse">
              Recherche en cours...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-2 pt-4 border-t">
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            checked={allowWebSearch}
            onChange={(e) => setAllowWebSearch(e.target.checked)}
          />
          Autoriser la recherche web (Wikipedia, Brave)
        </label>
        <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Votre question..."
          className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          Envoyer
        </button>
        </div>
      </form>
    </div>
  );
}

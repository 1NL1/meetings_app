import { useState, useEffect } from "react";
import client from "../api/client";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState([]);
  const [editing, setEditing] = useState(null);
  const [name, setName] = useState("");
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await client.get("/templates/");
      setTemplates(response.data);
    } finally {
      setLoading(false);
    }
  };

  const startCreate = () => {
    setEditing("new");
    setName("");
    setContent("");
  };

  const startEdit = (template) => {
    setEditing(template.id);
    setName(template.name);
    setContent(template.content);
  };

  const cancel = () => {
    setEditing(null);
    setName("");
    setContent("");
  };

  const save = async () => {
    if (editing === "new") {
      await client.post("/templates/", { name, content });
    } else {
      await client.put(`/templates/${editing}`, { name, content });
    }
    cancel();
    fetchTemplates();
  };

  const remove = async (id) => {
    await client.delete(`/templates/${id}`);
    fetchTemplates();
  };

  if (loading) return <p>Chargement...</p>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Templates</h1>
        <button
          onClick={startCreate}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Créer un template
        </button>
      </div>

      {editing && (
        <div className="border rounded-lg p-4 mb-6 bg-gray-50">
          <input
            type="text"
            placeholder="Nom du template"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full border rounded px-3 py-2 mb-3"
          />
          <textarea
            placeholder="Contenu Markdown du template..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="w-full border rounded px-3 py-2 h-48 font-mono text-sm"
          />
          <div className="flex gap-2 mt-3">
            <button
              onClick={save}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
            >
              Sauvegarder
            </button>
            <button
              onClick={cancel}
              className="px-4 py-2 border rounded"
            >
              Annuler
            </button>
          </div>
        </div>
      )}

      {templates.length === 0 && !editing ? (
        <p className="text-gray-500">Aucun template. Créez-en un pour commencer.</p>
      ) : (
        <div className="space-y-3">
          {templates.map((t) => (
            <div key={t.id} className="border rounded-lg p-4 flex justify-between items-start">
              <div className="flex-1">
                <h3 className="font-semibold">{t.name}</h3>
                <pre className="text-sm text-gray-500 mt-1 whitespace-pre-wrap line-clamp-3">
                  {t.content}
                </pre>
              </div>
              <div className="flex gap-2 ml-4">
                <button
                  onClick={() => startEdit(t)}
                  className="text-blue-600 hover:underline text-sm"
                >
                  Modifier
                </button>
                <button
                  onClick={() => remove(t.id)}
                  className="text-red-600 hover:underline text-sm"
                >
                  Supprimer
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

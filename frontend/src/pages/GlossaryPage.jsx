import { useState, useEffect } from "react";
import client from "../api/client";

const CATEGORIES = [
  { value: "", label: "Aucune" },
  { value: "person", label: "Personne" },
  { value: "company", label: "Entreprise" },
  { value: "project", label: "Projet" },
  { value: "acronym", label: "Acronyme" },
];

const CATEGORY_LABELS = {
  person: "Personne",
  company: "Entreprise",
  project: "Projet",
  acronym: "Acronyme",
};

const CATEGORY_COLORS = {
  person: "bg-blue-100 text-blue-700",
  company: "bg-purple-100 text-purple-700",
  project: "bg-green-100 text-green-700",
  acronym: "bg-orange-100 text-orange-700",
};

export default function GlossaryPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [term, setTerm] = useState("");
  const [category, setCategory] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchEntries();
  }, []);

  const fetchEntries = async () => {
    try {
      const res = await client.get("/glossary/");
      setEntries(res.data);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!term.trim()) return;
    setSubmitting(true);
    setError("");
    try {
      const res = await client.post("/glossary/", {
        term: term.trim(),
        category: category || null,
      });
      setEntries((prev) =>
        [...prev, res.data].sort((a, b) => {
          if (a.category === b.category) return a.term.localeCompare(b.term);
          return (a.category || "").localeCompare(b.category || "");
        })
      );
      setTerm("");
      setCategory("");
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur lors de l'ajout.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await client.delete(`/glossary/${id}`);
      setEntries((prev) => prev.filter((e) => e.id !== id));
    } catch {
      // ignore
    }
  };

  const grouped = entries.reduce((acc, entry) => {
    const key = entry.category || "other";
    if (!acc[key]) acc[key] = [];
    acc[key].push(entry);
    return acc;
  }, {});

  if (loading) return <p>Chargement...</p>;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Glossaire de noms propres</h1>
      <p className="text-sm text-gray-500 mb-6">
        Ces termes seront injectés dans le prompt de génération du compte-rendu pour que Mistral
        utilise les orthographes exactes, même si la transcription contient des variantes phonétiques.
      </p>

      <form onSubmit={handleSubmit} className="border rounded-lg p-4 mb-8 space-y-3 bg-gray-50">
        <h2 className="font-semibold text-gray-700">Ajouter un terme</h2>
        <div className="flex gap-3">
          <input
            type="text"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="Nom ou terme exact"
            className="flex-1 border rounded px-3 py-2 text-sm"
            required
          />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="border rounded px-3 py-2 text-sm"
          >
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={submitting || !term.trim()}
            className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
          >
            Ajouter
          </button>
        </div>
        {error && <p className="text-red-600 text-sm">{error}</p>}
      </form>

      {entries.length === 0 ? (
        <p className="text-gray-400 text-sm">Aucun terme dans le glossaire.</p>
      ) : (
        <div className="space-y-6">
          {Object.entries(grouped).map(([cat, items]) => (
            <div key={cat}>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                {CATEGORY_LABELS[cat] || "Sans catégorie"}
              </h3>
              <div className="border rounded-lg divide-y">
                {items.map((entry) => (
                  <div key={entry.id} className="flex items-center justify-between px-4 py-2">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium">{entry.term}</span>
                      {entry.category && (
                        <span
                          className={`text-xs px-2 py-0.5 rounded ${
                            CATEGORY_COLORS[entry.category] || "bg-gray-100 text-gray-600"
                          }`}
                        >
                          {CATEGORY_LABELS[entry.category]}
                        </span>
                      )}
                    </div>
                    <button
                      onClick={() => handleDelete(entry.id)}
                      className="text-gray-400 hover:text-red-500 text-sm"
                    >
                      Supprimer
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

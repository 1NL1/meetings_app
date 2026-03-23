import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api/client";

export default function DocumentsPage() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState([]);
  const [validatedMeetings, setValidatedMeetings] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [docType, setDocType] = useState("other");

  const fetchAll = useCallback(async () => {
    const [docRes, meetRes] = await Promise.all([
      api.get("/documents/"),
      api.get("/meetings/"),
    ]);
    setDocuments(docRes.data);
    setValidatedMeetings(meetRes.data.filter((m) => m.report_validated));
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      await api.post(`/documents/upload?doc_type=${docType}`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      await fetchAll();
    } catch (err) {
      alert("Erreur lors de l'upload : " + (err.response?.data?.detail || err.message));
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDoc = async (id) => {
    if (!confirm("Supprimer ce document ?")) return;
    await api.delete(`/documents/${id}`);
    await fetchAll();
  };

  const handleDeleteMeeting = async (id) => {
    if (!confirm("Supprimer cette réunion et son compte-rendu ?")) return;
    await api.delete(`/meetings/${id}`);
    await fetchAll();
  };

  const handleInvalidate = async (id) => {
    if (!confirm("Invalider ce compte-rendu ? Il redeviendra modifiable.")) return;
    await api.put(`/meetings/${id}/invalidate`);
    await fetchAll();
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Documents</h1>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="font-semibold mb-4">Uploader un document</h2>
        <div className="flex items-center gap-4">
          <select
            value={docType}
            onChange={(e) => setDocType(e.target.value)}
            className="border rounded px-3 py-2"
          >
            <option value="other">Autre</option>
            <option value="contract">Contrat</option>
            <option value="report">Bilan</option>
            <option value="minutes">PV de réunion</option>
          </select>
          <label className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
            {uploading ? "Upload en cours..." : "Choisir un fichier"}
            <input
              type="file"
              className="hidden"
              accept=".pdf,.png,.jpg,.jpeg,.webp,.docx,.txt,.md"
              onChange={handleUpload}
              disabled={uploading}
            />
          </label>
        </div>
      </div>

      {/* Validated meeting reports */}
      {validatedMeetings.length > 0 && (
        <div className="mb-6">
          <h2 className="font-semibold text-lg mb-3">Comptes-rendus validés</h2>
          <div className="space-y-3">
            {validatedMeetings.map((m) => (
              <div
                key={m.id}
                className="bg-white rounded-lg shadow p-4 flex items-center justify-between"
              >
                <div
                  className="flex-1 cursor-pointer"
                  onClick={() => navigate(`/meetings/${m.id}/report`)}
                >
                  <p className="font-medium">{m.title}</p>
                  <p className="text-sm text-gray-500">
                    Compte-rendu — {new Date(m.date).toLocaleDateString("fr-FR")}
                  </p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={() => handleInvalidate(m.id)}
                    className="text-orange-500 hover:text-orange-700 text-sm"
                  >
                    Invalider
                  </button>
                  <button
                    onClick={() => handleDeleteMeeting(m.id)}
                    className="text-red-500 hover:text-red-700 text-sm"
                  >
                    Supprimer
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Uploaded documents */}
      <div>
        <h2 className="font-semibold text-lg mb-3">Documents uploadés</h2>
        <div className="space-y-3">
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="bg-white rounded-lg shadow p-4 flex items-center justify-between"
            >
              <div>
                <p className="font-medium">{doc.filename}</p>
                <p className="text-sm text-gray-500">
                  {doc.doc_type} — {new Date(doc.created_at).toLocaleDateString("fr-FR")}
                </p>
                {doc.content_preview && (
                  <p className="text-sm text-gray-400 mt-1 truncate max-w-xl">
                    {doc.content_preview}
                  </p>
                )}
              </div>
              <button
                onClick={() => handleDeleteDoc(doc.id)}
                className="text-red-500 hover:text-red-700 text-sm"
              >
                Supprimer
              </button>
            </div>
          ))}
          {documents.length === 0 && (
            <p className="text-gray-400 text-center py-8">Aucun document uploadé.</p>
          )}
        </div>
      </div>
    </div>
  );
}

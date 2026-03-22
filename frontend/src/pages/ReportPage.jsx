import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import client from "../api/client";
import ReportEditor from "../components/ReportEditor";

export default function ReportPage() {
  const { id } = useParams();
  const [meeting, setMeeting] = useState(null);
  const [markdown, setMarkdown] = useState("");
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMeeting();
  }, [id]);

  const fetchMeeting = async () => {
    try {
      const response = await client.get(`/meetings/${id}`);
      setMeeting(response.data);
      setMarkdown(response.data.report_markdown || "");
    } finally {
      setLoading(false);
    }
  };

  const saveReport = async () => {
    setSaving(true);
    try {
      const response = await client.put(`/meetings/${id}/report`, {
        report_markdown: markdown,
      });
      setMeeting(response.data);
    } finally {
      setSaving(false);
    }
  };

  const validateReport = async () => {
    setSaving(true);
    try {
      const response = await client.put(`/meetings/${id}/validate`, {
        report_markdown: markdown,
      });
      setMeeting(response.data);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <p>Chargement...</p>;
  if (!meeting) return <p>Réunion introuvable.</p>;

  const isValidated = meeting.report_validated;

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-2xl font-bold">{meeting.title} — Compte-rendu</h1>
          {isValidated && (
            <span className="inline-block mt-1 bg-green-100 text-green-700 text-sm px-3 py-1 rounded">
              Validé
            </span>
          )}
        </div>
        {!isValidated && (
          <div className="flex gap-2">
            <button
              onClick={saveReport}
              disabled={saving}
              className="border px-4 py-2 rounded hover:bg-gray-50 disabled:opacity-50"
            >
              {saving ? "..." : "Sauvegarder"}
            </button>
            <button
              onClick={validateReport}
              disabled={saving}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              Valider
            </button>
          </div>
        )}
      </div>

      <ReportEditor
        value={markdown}
        onChange={setMarkdown}
        readOnly={isValidated}
      />
    </div>
  );
}

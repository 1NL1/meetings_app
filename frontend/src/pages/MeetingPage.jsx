import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import client from "../api/client";
import AudioUploader from "../components/AudioUploader";
import AudioRecorder from "../components/AudioRecorder";

export default function MeetingPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [meeting, setMeeting] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState("");
  const [generating, setGenerating] = useState(false);
  const [loading, setLoading] = useState(true);
  const [audioMode, setAudioMode] = useState("record");
  const [showTranscription, setShowTranscription] = useState(false);

  // Editable fields
  const [title, setTitle] = useState("");
  const [date, setDate] = useState("");
  const [participants, setParticipants] = useState("");
  const saveTimeout = useRef(null);

  useEffect(() => {
    fetchData();
  }, [id]);

  const fetchData = async () => {
    try {
      const [meetingRes, templatesRes] = await Promise.all([
        client.get(`/meetings/${id}`),
        client.get("/templates/"),
      ]);
      const m = meetingRes.data;
      setMeeting(m);
      setTitle(m.title);
      setDate(toLocalDatetime(m.date));
      setParticipants(m.participants || "");
      setTemplates(templatesRes.data);
      if (m.template_id) {
        setSelectedTemplate(m.template_id);
      }
    } finally {
      setLoading(false);
    }
  };

  const toLocalDatetime = (isoStr) => {
    const d = new Date(isoStr);
    const offset = d.getTimezoneOffset();
    const local = new Date(d.getTime() - offset * 60000);
    return local.toISOString().slice(0, 16);
  };

  const autoSave = (field, value) => {
    if (saveTimeout.current) clearTimeout(saveTimeout.current);
    saveTimeout.current = setTimeout(async () => {
      await client.put(`/meetings/${id}`, { [field]: value });
    }, 800);
  };

  const handleTitleChange = (e) => {
    const v = e.target.value;
    setTitle(v);
    autoSave("title", v);
  };

  const handleDateChange = (e) => {
    const v = e.target.value;
    setDate(v);
    autoSave("date", new Date(v).toISOString());
  };

  const handleParticipantsChange = (e) => {
    const v = e.target.value;
    setParticipants(v);
    autoSave("participants", v);
  };

  const onTranscriptionDone = (updatedMeeting) => {
    setMeeting((prev) => ({ ...prev, ...updatedMeeting }));
  };

  const generateReport = async () => {
    setGenerating(true);
    try {
      if (selectedTemplate !== (meeting.template_id || "")) {
        await client.put(`/meetings/${id}/template`, {
          template_id: selectedTemplate || null,
        });
      }
      const response = await client.post(`/meetings/${id}/generate-report`);
      setMeeting(response.data);
      navigate(`/meetings/${id}/report`);
    } finally {
      setGenerating(false);
    }
  };

  if (loading) return <p>Chargement...</p>;
  if (!meeting) return <p>Réunion introuvable.</p>;

  return (
    <div className="space-y-8">
      {/* Meeting info */}
      <section className="border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Informations</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Titre</label>
            <input
              type="text"
              value={title}
              onChange={handleTitleChange}
              className="border rounded px-3 py-2 w-full max-w-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Date</label>
            <input
              type="datetime-local"
              value={date}
              onChange={handleDateChange}
              className="border rounded px-3 py-2 w-full max-w-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Participants</label>
            <input
              type="text"
              value={participants}
              onChange={handleParticipantsChange}
              placeholder="Ex : Alice, Bob, Charlie"
              className="border rounded px-3 py-2 w-full max-w-md"
            />
            <p className="text-xs text-gray-400 mt-1">
              Séparés par des virgules. Transmis à Mistral pour le CR.
            </p>
          </div>
        </div>
      </section>

      {/* Audio Section */}
      <section className="border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Audio</h2>
        {meeting.raw_transcription ? (
          <div>
            <button
              onClick={() => setShowTranscription(!showTranscription)}
              className="flex items-center gap-2 text-green-600 font-medium hover:text-green-700"
            >
              <span className={`transition-transform ${showTranscription ? "rotate-90" : ""}`}>
                &#9654;
              </span>
              Transcription disponible
            </button>
            {showTranscription && (
              <div className="mt-3 bg-gray-50 rounded p-4 max-h-64 overflow-y-auto">
                <p className="whitespace-pre-wrap text-sm">{meeting.raw_transcription}</p>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex gap-2">
              <button
                onClick={() => setAudioMode("record")}
                className={`px-3 py-1 rounded text-sm ${
                  audioMode === "record"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-700"
                }`}
              >
                Enregistrer en direct
              </button>
              <button
                onClick={() => setAudioMode("upload")}
                className={`px-3 py-1 rounded text-sm ${
                  audioMode === "upload"
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-700"
                }`}
              >
                Uploader un fichier
              </button>
            </div>

            {audioMode === "record" ? (
              <AudioRecorder meetingId={id} onDone={onTranscriptionDone} />
            ) : (
              <AudioUploader meetingId={id} onDone={onTranscriptionDone} />
            )}
          </div>
        )}
      </section>

      {/* Report Section */}
      <section className="border rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Compte-rendu</h2>

        {meeting.report_markdown ? (
          <div>
            <span className="text-green-600 font-medium">
              {meeting.report_validated ? "CR validé" : "CR généré"}
            </span>
            <button
              onClick={() => navigate(`/meetings/${id}/report`)}
              className="ml-4 text-blue-600 hover:underline"
            >
              Voir / Modifier
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Template</label>
              <select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                className="border rounded px-3 py-2 w-full max-w-md"
              >
                <option value="">Template par défaut</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name}
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={generateReport}
              disabled={!meeting.raw_transcription || generating}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              {generating ? "Génération en cours..." : "Générer le CR"}
            </button>
            {!meeting.raw_transcription && (
              <p className="text-sm text-gray-500">
                Enregistrez ou uploadez un audio d'abord.
              </p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

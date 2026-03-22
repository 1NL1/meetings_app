import { useState } from "react";
import client from "../api/client";

export default function AudioUploader({ meetingId, onDone }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await client.post(
        `/meetings/${meetingId}/upload-audio`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      onDone(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Erreur lors de l'upload");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-3">
      <input
        type="file"
        accept="audio/*"
        onChange={(e) => setFile(e.target.files[0])}
        className="block"
      />
      {file && (
        <p className="text-sm text-gray-500">
          Fichier : {file.name}
        </p>
      )}
      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {uploading ? "Upload et transcription en cours..." : "Envoyer et transcrire"}
      </button>
      {error && <p className="text-red-600 text-sm">{error}</p>}
    </div>
  );
}

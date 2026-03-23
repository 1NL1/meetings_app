import { useState, useRef } from "react";

export default function AudioRecorder({ meetingId, onDone }) {
  const [recording, setRecording] = useState(false);
  const [transcription, setTranscription] = useState("");
  const [status, setStatus] = useState("");
  const mediaRecorderRef = useRef(null);
  const wsRef = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      mediaRecorderRef.current = mediaRecorder;

      // Open WebSocket
      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const ws = new WebSocket(
        `${wsProtocol}//${window.location.host}/api/meetings/${meetingId}/transcribe`
      );
      wsRef.current = ws;

      ws.onopen = () => {
        setRecording(true);
        setStatus("Enregistrement en cours...");
        mediaRecorder.start(1000); // Send a chunk every second
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "partial") {
          setTranscription(data.text);
          setStatus("Transcription partielle...");
        } else if (data.type === "final") {
          setTranscription(data.text);
          setStatus("Transcription terminée");
          if (onDone) {
            onDone({ raw_transcription: data.text });
          }
        }
      };

      ws.onerror = () => {
        setStatus("Erreur de connexion WebSocket");
        stopRecording();
      };

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
          ws.send(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        stream.getTracks().forEach((track) => track.stop());
      };
    } catch (err) {
      setStatus("Erreur : impossible d'accéder au microphone");
    }
  };

  const stopRecording = () => {
    setRecording(false);
    setStatus("Finalisation de la transcription...");

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }

    // Send empty bytes to signal end, then close
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(new ArrayBuffer(0));
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        {!recording ? (
          <button
            onClick={startRecording}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 flex items-center gap-2"
          >
            <span className="w-3 h-3 bg-white rounded-full" />
            Enregistrer
          </button>
        ) : (
          <button
            onClick={stopRecording}
            className="bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-800 flex items-center gap-2"
          >
            <span className="w-3 h-3 bg-red-500 rounded-sm animate-pulse" />
            Arrêter
          </button>
        )}
        {status && <span className="text-sm text-gray-500">{status}</span>}
      </div>

      {transcription && (
        <div className="bg-gray-50 rounded p-4 max-h-64 overflow-y-auto">
          <p className="text-xs text-gray-400 mb-1">Transcription en direct :</p>
          <p className="whitespace-pre-wrap text-sm">{transcription}</p>
        </div>
      )}
    </div>
  );
}

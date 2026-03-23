import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

export default function DashboardPage() {
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchMeetings();
  }, []);

  const fetchMeetings = async () => {
    try {
      const response = await client.get("/meetings/");
      setMeetings(response.data);
    } finally {
      setLoading(false);
    }
  };

  const createMeeting = async () => {
    const now = new Date();
    const title = `Réunion du ${now.toLocaleDateString("fr-FR")}`;
    const response = await client.post("/meetings/", {
      title,
      date: now.toISOString(),
    });
    navigate(`/meetings/${response.data.id}`);
  };

  const getBadges = (meeting) => {
    const badges = [];
    if (meeting.raw_transcription) badges.push("Transcrit");
    if (meeting.report_markdown) badges.push("CR généré");
    if (meeting.report_validated) badges.push("Validé");
    return badges;
  };

  if (loading) return <p>Chargement...</p>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Mes réunions</h1>
        <button
          onClick={createMeeting}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          Nouvelle réunion
        </button>
      </div>

      {meetings.length === 0 ? (
        <p className="text-gray-500">Aucune réunion pour le moment.</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {meetings.map((m) => (
            <div
              key={m.id}
              onClick={() => navigate(`/meetings/${m.id}`)}
              className="border rounded-lg p-4 hover:shadow-md cursor-pointer"
            >
              <h3 className="font-semibold text-lg">{m.title}</h3>
              <p className="text-sm text-gray-500">
                {new Date(m.date).toLocaleDateString("fr-FR")}
              </p>
              <div className="flex gap-2 mt-2">
                {getBadges(m).map((badge) => (
                  <span
                    key={badge}
                    className="text-xs px-2 py-1 rounded bg-green-100 text-green-700"
                  >
                    {badge}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

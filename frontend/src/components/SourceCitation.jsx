import { useNavigate } from "react-router-dom";

export default function SourceCitation({ source }) {
  const navigate = useNavigate();

  const handleClick = () => {
    if (source.source_type === "meeting") {
      navigate(`/meetings/${source.source_id}/report`);
    } else if (source.source_type === "document") {
      navigate(`/documents`);
    }
  };

  const icon = source.source_type === "meeting" ? "CR" : "Doc";
  const score = Math.round(source.relevance_score * 100);

  return (
    <button
      onClick={handleClick}
      className="text-left w-full border rounded p-3 hover:bg-gray-50 transition"
    >
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-bold bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
          {icon}
        </span>
        <span className="font-medium text-sm">{source.source_name}</span>
        <span className="text-xs text-gray-400 ml-auto">{score}%</span>
      </div>
      <p className="text-sm text-gray-600 line-clamp-2">{source.chunk_text}</p>
    </button>
  );
}

import ReactMarkdown from "react-markdown";

export default function ReportEditor({ value, onChange, readOnly }) {
  return (
    <div className="grid grid-cols-2 gap-4 h-[calc(100vh-200px)]">
      {/* Editor */}
      <div className="border rounded-lg overflow-hidden flex flex-col">
        <div className="bg-gray-100 px-3 py-2 text-sm font-medium border-b">
          Markdown
        </div>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          readOnly={readOnly}
          className="flex-1 p-4 font-mono text-sm resize-none focus:outline-none disabled:bg-gray-50"
          disabled={readOnly}
        />
      </div>

      {/* Preview */}
      <div className="border rounded-lg overflow-hidden flex flex-col">
        <div className="bg-gray-100 px-3 py-2 text-sm font-medium border-b">
          Aperçu
        </div>
        <div className="flex-1 p-4 overflow-y-auto prose prose-sm max-w-none">
          <ReactMarkdown>{value}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

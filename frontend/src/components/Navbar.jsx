import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

export default function Navbar() {
  const { logout } = useAuth();

  return (
    <nav className="bg-white border-b">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-14">
        <div className="flex items-center gap-6">
          <Link to="/" className="font-bold text-lg text-blue-600">
            MeetWise
          </Link>
          <Link to="/" className="text-gray-600 hover:text-gray-900">
            Dashboard
          </Link>
          <Link to="/templates" className="text-gray-600 hover:text-gray-900">
            Templates
          </Link>
          <Link to="/documents" className="text-gray-600 hover:text-gray-900">
            Documents
          </Link>
          <Link to="/chat" className="text-gray-600 hover:text-gray-900">
            Chat
          </Link>
        </div>
        <button
          onClick={logout}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          Déconnexion
        </button>
      </div>
    </nav>
  );
}

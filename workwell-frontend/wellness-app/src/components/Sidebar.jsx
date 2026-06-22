import { Link, useLocation } from "react-router-dom";

function Sidebar() {

  const location = useLocation();

  const role = localStorage.getItem("role");

  return (

    <div className="w-72 min-h-screen bg-[#38240D] text-white flex flex-col p-6">

      <div className="mb-12">

        <h1 className="text-4xl font-bold">
          WorkWell
        </h1>

        <p className="text-gray-300 mt-2">
          AI Wellness Platform
        </p>

      </div>

      <div className="space-y-3">

        {role === "employee" && (
          <>
            <Link
              to="/dashboard"
              className={`block p-4 rounded-xl ${
                location.pathname === "/dashboard"
                  ? "bg-[#C05800]"
                  : "hover:bg-[#713600]"
              }`}
            >
              Dashboard
            </Link>

            <Link
              to="/wellness"
              className={`block p-4 rounded-xl ${
                location.pathname === "/wellness"
                  ? "bg-[#C05800]"
                  : "hover:bg-[#713600]"
              }`}
            >
              Wellness Form
            </Link>

            <Link
              to="/history"
              className={`block p-4 rounded-xl ${
                location.pathname === "/history"
                  ? "bg-[#C05800]"
                  : "hover:bg-[#713600]"
              }`}
            >
              History
            </Link>
          </>
        )}

        {role === "manager" && (

          <Link
            to="/manager"
            className={`block p-4 rounded-xl ${
              location.pathname === "/manager"
                ? "bg-[#C05800]"
                : "hover:bg-[#713600]"
            }`}
          >
            Manager Dashboard
          </Link>

        )}

      </div>

      <div className="mt-auto">

        <button
          onClick={() => {

            localStorage.clear();

            window.location.href = "/";

          }}
          className="w-full bg-[#C05800] py-3 rounded-xl"
        >
          Logout
        </button>

      </div>

    </div>

  );
}

export default Sidebar;
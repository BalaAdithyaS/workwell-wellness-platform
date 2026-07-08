import { NavLink, Outlet, useNavigate } from "react-router-dom";

function EmployeeLayout() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.clear();
    navigate("/");
  };

  const linkClass = ({ isActive }) =>
    `block w-full px-5 py-4 rounded-2xl font-medium transition-all duration-300 ${
      isActive
        ? "bg-[#C05800] text-white shadow-md"
        : "text-[#FDFBD4] hover:bg-[#713600]"
    }`;

  return (
    <div className="min-h-screen bg-[#FDFBD4]">

      {/* Shared Employee Sidebar */}
      <aside className="fixed left-0 top-0 w-72 h-screen bg-[#38240D] text-[#FDFBD4] p-6 flex flex-col z-50">

        {/* Branding */}
        <div className="mb-12">
          <h1 className="text-4xl font-bold tracking-tight">
            WorkWell
          </h1>

          <p className="text-sm text-gray-300 mt-2">
            AI Wellness Platform
          </p>
        </div>

        {/* Navigation */}
        <nav className="space-y-3">

          <NavLink
            to="/dashboard"
            className={linkClass}
          >
            Dashboard
          </NavLink>

          <NavLink
            to="/wellness"
            className={linkClass}
          >
            Wellness Form
          </NavLink>

          <NavLink
            to="/history"
            className={linkClass}
          >
            Wellness History
          </NavLink>

          <NavLink
            to="/voice"
            className={linkClass}
          >
            Voice Wellness Coach
          </NavLink>

        </nav>

        {/* Bottom Section */}
        <div className="mt-auto">

          <div className="pt-6 mb-6 border-t border-[#713600]">
            <p className="text-sm text-gray-300">
              Logged in as
            </p>

            <p className="font-semibold text-lg mt-1">
              {localStorage.getItem("name") || "Employee"}
            </p>
          </div>

          <button
            onClick={handleLogout}
            className="w-full px-5 py-4 rounded-2xl bg-[#C05800] text-white font-semibold hover:bg-[#713600] transition-all duration-300"
          >
            Logout
          </button>

        </div>

      </aside>

      {/* All Employee Pages */}
      <main className="ml-72 min-h-screen">
        <Outlet />
      </main>

    </div>
  );
}

export default EmployeeLayout;
import { useEffect, useState } from "react";
import API from "../services/api";
import { useNavigate } from "react-router-dom";

function ManagerDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (localStorage.getItem("role") !== "manager") {
      navigate("/dashboard");
      return;
    }

    fetchManagerData();
  }, []);

  const fetchManagerData = async () => {
    try {
      setLoading(true);
      const response = await API.get("/manager/dashboard");
      setData(response.data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  if (loading || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FDFBD4]">
        <h1 className="text-2xl font-semibold text-[#38240D]">
          Loading Manager Dashboard...
        </h1>
      </div>
    );
  }

  const employees = data.employee_summaries || [];

  const filteredEmployees = employees.filter((emp) =>
    emp.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-[#FDFBD4] p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-10">
        <div>
          <h1 className="text-5xl font-bold text-[#38240D]">Manager Dashboard</h1>
          <p className="text-[#713600] mt-2">Workforce wellness overview for {data.company}</p>
        </div>
        <button
          onClick={() => {
            localStorage.clear();
            navigate("/");
          }}
          className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-xl"
        >
          Logout
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-3xl p-6 shadow-lg hover:shadow-xl transition duration-300">
          <p className="text-sm uppercase tracking-wide text-[#713600]">Total Employees</p>
          <h2 className="text-5xl font-bold text-[#38240D] mt-3">{data.total_employees}</h2>
          <p className="text-sm text-gray-500 mt-3">Active workforce</p>
        </div>
        <div className="bg-white rounded-3xl p-6 shadow-lg hover:shadow-xl transition duration-300">
          <p className="text-sm uppercase tracking-wide text-[#713600]">Average Mood</p>
          <h2 className="text-5xl font-bold text-green-600 mt-3">{data.avg_mood}</h2>
          <p className="text-sm text-gray-500 mt-3">Overall team morale</p>
        </div>
        <div className="bg-white rounded-3xl p-6 shadow-lg hover:shadow-xl transition duration-300">
          <p className="text-sm uppercase tracking-wide text-[#713600]">Average Stress</p>
          <h2 className="text-5xl font-bold text-yellow-600 mt-3">{data.avg_stress}</h2>
          <p className="text-sm text-gray-500 mt-3">Current stress level</p>
        </div>
        <div className="bg-white rounded-3xl p-6 shadow-lg hover:shadow-xl transition duration-300">
          <p className="text-sm uppercase tracking-wide text-[#713600]">High Burnout Cases</p>
          <h2 className="text-5xl font-bold text-red-600 mt-3">{data.burnout_high_count}</h2>
          <p className="text-sm text-gray-500 mt-3">Employees requiring attention</p>
        </div>
      </div>

      {/* AI Workforce Insight */}
      <div className="bg-white rounded-3xl shadow-lg p-8 mb-8 border-l-[8px] border-[#C05800]">
        <h2 className="text-2xl font-bold text-[#38240D] mb-6">AI Workforce Insight</h2>
        <div className="space-y-5">
          <div className="bg-[#FDFBD4] rounded-2xl p-5">
            <h3 className="font-semibold text-[#38240D] mb-2">Workforce Summary</h3>
            <p className="text-[#713600]">
              Average Mood Score: <strong>{data.avg_mood}</strong>
            </p>
            <p className="text-[#713600]">
              Average Stress Level: <strong>{data.avg_stress}</strong>
            </p>
            <p className="text-[#713600]">
              High Burnout Employees: <strong>{data.burnout_high_count}</strong>
            </p>
          </div>
          <div className="bg-blue-50 rounded-2xl p-5">
            <h3 className="font-semibold text-blue-800 mb-2">AI Observation</h3>
            <p className="text-gray-700">
              {data.avg_mood >= 7
                ? "Employee morale is healthy and the workforce appears engaged."
                : "Overall morale has decreased and requires manager attention."}
            </p>
            <p className="text-gray-700 mt-2">
              {data.avg_stress >= 4
                ? "Stress levels are above the recommended threshold. Monitoring and workload balancing are advised."
                : "Stress levels remain within an acceptable range."}
            </p>
          </div>
          <div className="bg-green-50 rounded-2xl p-5">
            <h3 className="font-semibold text-green-800 mb-2">Recommendation</h3>
            <p className="text-gray-700">
              {data.burnout_high_count > 0
                ? "Schedule one-on-one meetings with high-risk employees, redistribute workloads where necessary, and encourage wellness breaks."
                : "Continue regular wellness assessments and maintain current employee engagement initiatives."}
            </p>
          </div>
        </div>
      </div>

      {/* Risk Alert */}
      {data.burnout_high_count > 0 && (
        <div className="bg-white rounded-3xl shadow-lg p-8 mb-8 border-l-[10px] border-red-500">
          <h2 className="text-2xl font-bold text-red-600 mb-3">Burnout Risk Alert</h2>
          <p className="text-[#38240D]">
            {data.burnout_high_count} employee(s) currently exhibit elevated burnout
            indicators. Immediate review and manager intervention are recommended.
          </p>
        </div>
      )}

      {/* Workforce Health Summary */}
      <div className="bg-white rounded-3xl shadow-lg p-8">
        <h2 className="text-2xl font-bold text-[#38240D] mb-6">Workforce Health Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-[#FDFBD4] rounded-2xl p-5">
            <h3 className="font-semibold text-[#38240D] mb-2">Wellness Status</h3>
            <p className="text-[#713600]">
              {data.avg_mood >= 7 ? "Healthy" : "Requires Monitoring"}
            </p>
          </div>
          <div className="bg-[#FDFBD4] rounded-2xl p-5">
            <h3 className="font-semibold text-[#38240D] mb-2">Stress Status</h3>
            <p className="text-[#713600]">
              {data.avg_stress >= 4 ? "Elevated" : "Normal"}
            </p>
          </div>
          <div className="bg-[#FDFBD4] rounded-2xl p-5">
            <h3 className="font-semibold text-[#38240D] mb-2">Burnout Exposure</h3>
            <p className="text-[#713600]">
              {data.burnout_high_count > 0 ? "High" : "Low"}
            </p>
          </div>
        </div>
      </div>

      {/* All Employees Table */}
      <div className="bg-white rounded-3xl shadow-lg p-8 mt-8">
        <h2 className="text-2xl font-bold text-[#38240D] mb-6">Team Employees</h2>
        <input
          type="text"
          placeholder="Search employee..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full p-3 mb-6 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#C05800]"
        />

        {filteredEmployees.length === 0 ? (
          <p className="text-[#713600] text-center py-8">No employees found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-[#FFF8D6] border-b">
                  <th className="text-left py-4 px-4 font-semibold text-[#38240D]">Employee</th>
                  <th className="text-left py-4 px-4 font-semibold text-[#38240D]">Entries</th>
                  <th className="text-left py-4 px-4 font-semibold text-[#38240D]">Avg Mood</th>
                  <th className="text-left py-4 px-4 font-semibold text-[#38240D]">Avg Stress</th>
                  <th className="text-left py-4 px-4 font-semibold text-[#38240D]">Avg Burnout</th>
                  <th className="text-left py-4 px-4 font-semibold text-[#38240D]">Sentiment</th>
                  <th className="text-left py-4 px-4 font-semibold text-[#38240D]">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredEmployees.map((emp) => (
                  <tr
                    key={emp.user_id}
                    className="border-b hover:bg-[#FFF8D6] transition duration-200"
                  >
                    <td className="py-4 px-4 font-medium text-[#38240D]">{emp.name}</td>
                    <td className="py-4 px-4 text-gray-600">{emp.entries}</td>
                    <td className="py-4 px-4">
                      <span
                        className={`font-bold ${
                          emp.avg_mood >= 7
                            ? "text-green-600"
                            : emp.avg_mood >= 4
                            ? "text-yellow-600"
                            : "text-red-600"
                        }`}
                      >
                        {emp.avg_mood}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span
                        className={`font-bold ${
                          emp.avg_stress <= 2
                            ? "text-green-600"
                            : emp.avg_stress <= 4
                            ? "text-yellow-600"
                            : "text-red-600"
                        }`}
                      >
                        {emp.avg_stress}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span
                        className={`font-bold ${
                          emp.avg_burnout >= 5
                            ? "text-red-600"
                            : emp.avg_burnout >= 3
                            ? "text-yellow-600"
                            : "text-green-600"
                        }`}
                      >
                        {emp.avg_burnout}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      {emp.latest_sentiment ? (
                        <span
                          className={`px-3 py-1 rounded-full text-sm font-medium ${
                            emp.latest_sentiment.toLowerCase() === "positive"
                              ? "bg-green-100 text-green-700"
                              : emp.latest_sentiment.toLowerCase() === "neutral"
                              ? "bg-yellow-100 text-yellow-700"
                              : "bg-red-100 text-red-700"
                          }`}
                        >
                          {emp.latest_sentiment}
                        </span>
                      ) : (
                        <span className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-sm font-medium">
                          No Data
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-4">
                      {emp.burnout_risk_level === "high" ? (
                        <span className="bg-red-100 text-red-700 px-3 py-1 rounded-full text-sm font-semibold">
                          Critical
                        </span>
                      ) : emp.burnout_risk_level === "medium" ? (
                        <span className="bg-yellow-100 text-yellow-700 px-3 py-1 rounded-full text-sm font-semibold">
                          Monitor
                        </span>
                      ) : (
                        <span className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-semibold">
                          Healthy
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default ManagerDashboard;

import { useEffect, useState } from "react";
import API from "../services/api";
import { useNavigate } from "react-router-dom";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
} from "recharts";
function ManagerDashboard() {
    const [data, setData] = useState(null);
    const [highRiskEmployees, setHighRiskEmployees] = useState([]); 
    const [trendData, setTrendData] = useState([]);
    const navigate = useNavigate();
    const [search,setSearch]=useState("");
useEffect(()=>{

   if(localStorage.getItem("role")!=="manager"){
      navigate("/dashboard");
      return;
   }

   fetchManagerData();
   fetchHighRiskEmployees();
   fetchTeamTrends();

   const interval=setInterval(()=>{
      fetchManagerData();
      fetchHighRiskEmployees();
      fetchTeamTrends();
   },30000);

   return ()=>clearInterval(interval);

},[]);

  const fetchManagerData = async () => {
    try {
      const teamId = localStorage.getItem("team_id");

      const response = await API.get(
          "/analytics/manager-summary",
      {
        params: {
        team_id: teamId,
        },
  }
);

      setData(response.data);

    } catch (error) {
      console.error(error);
    }
  };
const fetchHighRiskEmployees = async () => {
  try {
    const teamId = localStorage.getItem("team_id");

    const response = await API.get(
      "/analytics/all-employees",
      {
        params: {
          team_id: teamId,
        },
      }
    );

    setHighRiskEmployees(response.data);

  } catch (error) {
    console.error(error);
  }
};
const fetchTeamTrends = async () => {
  try {
    const teamId = localStorage.getItem("team_id");

    const response = await API.get(
      "/analytics/team-trends",
      {
        params: {
          team_id: teamId,
        },
      }
    );

    setTrendData(response.data);

  } catch (error) {
    console.error(error);
  }
};

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FDFBD4]">
        <h1 className="text-2xl font-semibold text-[#38240D]">
          Loading Manager Dashboard...
        </h1>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FDFBD4] p-8">

      {/* Header */}
      <div className="flex justify-between items-center mb-10">

  <div>

    <h1 className="text-5xl font-bold text-[#38240D]">
      Manager Dashboard
    </h1>

    <p className="text-[#713600] mt-2">
      Workforce wellness overview.
    </p>

  </div>

  <button
    onClick={()=>{
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

  {/* Total Employees */}
  <div className="bg-white rounded-3xl p-6 shadow-lg hover:shadow-xl transition duration-300">

    <p className="text-sm uppercase tracking-wide text-[#713600]">
      Total Employees
    </p>

    <h2 className="text-5xl font-bold text-[#38240D] mt-3">
      {data.total_employees}
    </h2>

    <p className="text-sm text-gray-500 mt-3">
      Active workforce
    </p>

  </div>

  {/* Average Mood */}
  <div className="bg-white rounded-3xl p-6 shadow-lg hover:shadow-xl transition duration-300">

    <p className="text-sm uppercase tracking-wide text-[#713600]">
      Average Mood
    </p>

    <h2 className="text-5xl font-bold text-green-600 mt-3">
      {data.average_mood}
    </h2>

    <p className="text-sm text-gray-500 mt-3">
      Overall team morale
    </p>

  </div>

  {/* Average Stress */}
  <div className="bg-white rounded-3xl p-6 shadow-lg hover:shadow-xl transition duration-300">

    <p className="text-sm uppercase tracking-wide text-[#713600]">
      Average Stress
    </p>

    <h2 className="text-5xl font-bold text-yellow-600 mt-3">
      {data.average_stress}
    </h2>

    <p className="text-sm text-gray-500 mt-3">
      Current stress level
    </p>

  </div>

  {/* Burnout */}
  <div className="bg-white rounded-3xl p-6 shadow-lg hover:shadow-xl transition duration-300">

    <p className="text-sm uppercase tracking-wide text-[#713600]">
      High Burnout Cases
    </p>

    <h2 className="text-5xl font-bold text-red-600 mt-3">
      {data.high_burnout}
    </h2>

    <p className="text-sm text-gray-500 mt-3">
      Employees requiring attention
    </p>

  </div>

</div>

      {/* AI Workforce Insight */}

<div className="bg-white rounded-3xl shadow-lg p-8 mb-8 border-l-[8px] border-[#C05800]">

  <h2 className="text-2xl font-bold text-[#38240D] mb-6">
    AI Workforce Insight
  </h2>

  <div className="space-y-5">

    <div className="bg-[#FDFBD4] rounded-2xl p-5">

      <h3 className="font-semibold text-[#38240D] mb-2">
        Workforce Summary
      </h3>

      <p className="text-[#713600]">
        • Average Mood Score: <strong>{data.average_mood}</strong>
      </p>

      <p className="text-[#713600]">
        • Average Stress Level: <strong>{data.average_stress}</strong>
      </p>

      <p className="text-[#713600]">
        • High Burnout Employees: <strong>{data.high_burnout}</strong>
      </p>

    </div>

    <div className="bg-blue-50 rounded-2xl p-5">

      <h3 className="font-semibold text-blue-800 mb-2">
        AI Observation
      </h3>

      <p className="text-gray-700">

        {data.average_mood >= 7
          ? "Employee morale is healthy and the workforce appears engaged."
          : "Overall morale has decreased and requires manager attention."}

      </p>

      <p className="text-gray-700 mt-2">

        {data.average_stress >= 4
          ? "Stress levels are above the recommended threshold. Monitoring and workload balancing are advised."
          : "Stress levels remain within an acceptable range."}

      </p>

    </div>

    <div className="bg-green-50 rounded-2xl p-5">

      <h3 className="font-semibold text-green-800 mb-2">
        Recommendation
      </h3>

      <p className="text-gray-700">

        {data.high_burnout > 0
          ? "Schedule one-on-one meetings with high-risk employees, redistribute workloads where necessary, and encourage wellness breaks."
          : "Continue regular wellness assessments and maintain current employee engagement initiatives."}

      </p>

    </div>

  </div>

</div>

      {/* Risk Alert */}
      {data.high_burnout > 0 && (

        <div className="bg-white rounded-3xl shadow-lg p-8 mb-8 border-l-[10px] border-red-500">

          <h2 className="text-2xl font-bold text-red-600 mb-3">
            Burnout Risk Alert
          </h2>

          <p className="text-[#38240D]">
            {data.high_burnout} employee(s) currently exhibit elevated burnout indicators.
            Immediate review and manager intervention are recommended.
          </p>

        </div>

      )}

      {/* Workforce Health Summary */}
      <div className="bg-white rounded-3xl shadow-lg p-8">

        <h2 className="text-2xl font-bold text-[#38240D] mb-6">
          Workforce Health Summary
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

          <div className="bg-[#FDFBD4] rounded-2xl p-5">
            <h3 className="font-semibold text-[#38240D] mb-2">
              Wellness Status
            </h3>

            <p className="text-[#713600]">
              {data.average_mood >= 7
                ? "Healthy"
                : "Requires Monitoring"}
            </p>
          </div>

          <div className="bg-[#FDFBD4] rounded-2xl p-5">
            <h3 className="font-semibold text-[#38240D] mb-2">
              Stress Status
            </h3>

            <p className="text-[#713600]">
              {data.average_stress >= 4
                ? "Elevated"
                : "Normal"}
            </p>
          </div>

          <div className="bg-[#FDFBD4] rounded-2xl p-5">
            <h3 className="font-semibold text-[#38240D] mb-2">
              Burnout Exposure
            </h3>

            <p className="text-[#713600]">
              {data.high_burnout > 0
                ? "High"
                : "Low"}
            </p>
          </div>

        </div>

      </div>
{/* All Employees */}
<div className="bg-white rounded-3xl shadow-lg p-8 mt-8">

  <h2 className="text-2xl font-bold text-[#38240D] mb-6">
    Team Employees
  </h2>

  <input
    type="text"
    placeholder="Search employee..."
    value={search}
    onChange={(e) => setSearch(e.target.value)}
    className="w-full p-3 mb-6 rounded-xl border border-gray-300 focus:outline-none focus:ring-2 focus:ring-[#C05800]"
  />

  {highRiskEmployees.length === 0 ? (

    <p className="text-[#713600] text-center py-8">
      No employees found in this team.
    </p>

  ) : (

    <div className="overflow-x-auto">

      <table className="w-full border-collapse">

        <thead>

          <tr className="bg-[#FFF8D6] border-b">

            <th className="text-left py-4 px-4 font-semibold text-[#38240D]">
              Employee
            </th>

            <th className="text-left py-4 px-4 font-semibold text-[#38240D]">
              Email
            </th>

            <th className="text-left py-4 px-4 font-semibold text-[#38240D]">
              Mood
            </th>

            <th className="text-left py-4 px-4 font-semibold text-[#38240D]">
              Stress
            </th>

            <th className="text-left py-4 px-4 font-semibold text-[#38240D]">
              Burnout
            </th>

            <th className="text-left py-4 px-4 font-semibold text-[#38240D]">
              Sentiment
            </th>

            <th className="text-left py-4 px-4 font-semibold text-[#38240D]">
              Status
            </th>

          </tr>

        </thead>

        <tbody>

          {highRiskEmployees.filter((employee) =>
            employee.name
              .toLowerCase()
              .includes(search.toLowerCase())
          ).length === 0 ? (

            <tr>
              <td
                colSpan={7}
                className="text-center py-10 text-gray-500"
              >
                No employees match your search.
              </td>
            </tr>

          ) : (

            highRiskEmployees
              .filter((employee) =>
                employee.name
                  .toLowerCase()
                  .includes(search.toLowerCase())
              )
              .map((employee, index) => (

                <tr
                  key={employee.email || index}
                  className="border-b hover:bg-[#FFF8D6] transition duration-200"
                >

                  {/* Employee */}
                  <td className="py-4 px-4 font-medium text-[#38240D]">
                    {employee.name}
                  </td>

                  {/* Email */}
                  <td className="py-4 px-4 text-gray-600">
                    {employee.email}
                  </td>

                  {/* Mood */}
                  <td className="py-4 px-4">

                    {employee.mood_score == null ? (

                      <span className="text-gray-400">
                        —
                      </span>

                    ) : (

                      <span
                        className={`font-bold ${
                          employee.mood_score >= 7
                            ? "text-green-600"
                            : employee.mood_score >= 4
                            ? "text-yellow-600"
                            : "text-red-600"
                        }`}
                      >
                        {employee.mood_score}
                      </span>

                    )}

                  </td>

                  {/* Stress */}
                  <td className="py-4 px-4">

                    {employee.stress_level == null ? (

                      <span className="text-gray-400">
                        —
                      </span>

                    ) : (

                      <span
                        className={`font-bold ${
                          employee.stress_level <= 2
                            ? "text-green-600"
                            : employee.stress_level <= 4
                            ? "text-yellow-600"
                            : "text-red-600"
                        }`}
                      >
                        {employee.stress_level}
                      </span>

                    )}

                  </td>

                  {/* Burnout */}
                  <td className="py-4 px-4">

                    {employee.burnout_risk == null ? (

                      <span className="text-gray-400">
                        —
                      </span>

                    ) : (

                      <span
                        className={`font-bold ${
                          employee.burnout_risk >= 5
                            ? "text-red-600"
                            : employee.burnout_risk >= 3
                            ? "text-yellow-600"
                            : "text-green-600"
                        }`}
                      >
                        {employee.burnout_risk}
                      </span>

                    )}

                  </td>

                  {/* Sentiment */}
                  <td className="py-4 px-4">

                    {employee.sentiment === "No data" ? (

                      <span className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-sm font-medium">
                        No Data
                      </span>

                    ) : (

                      <span
                        className={`px-3 py-1 rounded-full text-sm font-medium ${
                          employee.sentiment === "Positive"
                            ? "bg-green-100 text-green-700"
                            : employee.sentiment === "Neutral"
                            ? "bg-yellow-100 text-yellow-700"
                            : "bg-red-100 text-red-700"
                        }`}
                      >
                        {employee.sentiment || "Unknown"}
                      </span>

                    )}

                  </td>

                  {/* Status */}
                  <td className="py-4 px-4">

                    {employee.burnout_risk == null ? (

                      <span className="bg-gray-100 text-gray-600 px-3 py-1 rounded-full text-sm font-semibold">
                        No Data
                      </span>

                    ) : employee.burnout_risk >= 5 ? (

                      <span className="bg-red-100 text-red-700 px-3 py-1 rounded-full text-sm font-semibold">
                        Critical
                      </span>

                    ) : employee.burnout_risk >= 3 ? (

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

              ))

          )}

        </tbody>

      </table>

    </div>

  )}

</div>

    </div>
  );
}

export default ManagerDashboard;
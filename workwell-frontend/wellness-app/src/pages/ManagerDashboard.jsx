import { useEffect, useState } from "react";
import API from "../services/api";
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
useEffect(() => {
  fetchManagerData();
  fetchHighRiskEmployees();
  fetchTeamTrends();
}, []);

  const fetchManagerData = async () => {
    try {
      const response = await API.get(
        "/analytics/manager-summary"
      );

      setData(response.data);

    } catch (error) {
      console.error(error);
    }
  };
  const fetchHighRiskEmployees = async () => {
  try {

    const response = await API.get(
      "/analytics/high-risk-employees"
    );

    setHighRiskEmployees(
      response.data
    );

  } catch (error) {

    console.error(error);

  }
};
const fetchTeamTrends = async () => {
  try {

    const response = await API.get(
      "/analytics/team-trends"
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
      <div className="mb-10">

        <h1 className="text-5xl font-bold text-[#38240D]">
          Manager Dashboard
        </h1>

        <p className="text-[#713600] mt-2">
          Workforce wellness overview and risk monitoring.
        </p>

      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">

        <div className="bg-white rounded-3xl p-6 shadow-lg">
          <p className="text-sm uppercase tracking-wide text-[#713600]">
            Total Employees
          </p>

          <h2 className="text-5xl font-bold text-[#38240D] mt-3">
            {data.total_employees}
          </h2>
        </div>

        <div className="bg-white rounded-3xl p-6 shadow-lg">
          <p className="text-sm uppercase tracking-wide text-[#713600]">
            Average Mood
          </p>

          <h2 className="text-5xl font-bold text-[#38240D] mt-3">
            {data.average_mood}
          </h2>
        </div>

        <div className="bg-white rounded-3xl p-6 shadow-lg">
          <p className="text-sm uppercase tracking-wide text-[#713600]">
            Average Stress
          </p>

          <h2 className="text-5xl font-bold text-[#38240D] mt-3">
            {data.average_stress}
          </h2>
        </div>

        <div className="bg-white rounded-3xl p-6 shadow-lg">
          <p className="text-sm uppercase tracking-wide text-[#713600]">
            High Burnout Cases
          </p>

          <h2 className="text-5xl font-bold text-red-600 mt-3">
            {data.high_burnout}
          </h2>
        </div>

      </div>

      {/* AI Insight */}
      <div className="bg-white rounded-3xl shadow-lg p-8 mb-8 border-l-[10px] border-[#C05800]">

        <h2 className="text-2xl font-bold text-[#38240D] mb-6">
          AI Workforce Insight
        </h2>

        <div className="space-y-4 text-[#713600]">

          <p>
            {data.average_mood >= 7
              ? "Employee engagement and morale remain healthy across recent wellness submissions."
              : "Employee morale indicates potential wellness concerns requiring attention."}
          </p>

          <p>
            {data.average_stress >= 4
              ? "Stress indicators are above the recommended threshold and should be monitored closely."
              : "Stress indicators remain within an acceptable range."}
          </p>

          <div className="bg-[#FDFBD4] rounded-2xl p-5 text-[#38240D]">

            <span className="font-semibold">
              Recommendation:
            </span>

            {data.high_burnout > 0
              ? " Conduct manager check-ins, review workload allocation, and encourage recovery time for affected employees."
              : " Continue current wellness initiatives and maintain periodic employee wellness assessments."}

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
      <div className="bg-white rounded-3xl shadow-lg p-8 mt-8">

  <h2 className="text-2xl font-bold text-[#38240D] mb-6">
    Team Wellness Trends
  </h2>

  <ResponsiveContainer
    width="100%"
    height={350}
  >

    <LineChart data={trendData}>

      <XAxis dataKey="date" />

      <YAxis />

      <Tooltip />

      <Legend />

      <Line
        type="monotone"
        dataKey="mood"
        stroke="#16a34a"
        strokeWidth={3}
        name="Mood"
      />

      <Line
        type="monotone"
        dataKey="stress"
        stroke="#f59e0b"
        strokeWidth={3}
        name="Stress"
      />

      <Line
        type="monotone"
        dataKey="burnout"
        stroke="#dc2626"
        strokeWidth={3}
        name="Burnout"
      />

    </LineChart>

  </ResponsiveContainer>

</div>
      <div className="bg-white rounded-3xl shadow-lg p-8 mt-8">

  <h2 className="text-2xl font-bold text-[#38240D] mb-6">
    Employees Requiring Attention
  </h2>

  {highRiskEmployees.length === 0 ? (

    <p className="text-[#713600]">
      No high-risk employees detected.
    </p>

  ) : (

    <table className="w-full">

      <thead>

        <tr className="border-b">

          <th className="text-left py-4">
            Employee
          </th>

          <th className="text-left py-4">
            Mood
          </th>

          <th className="text-left py-4">
            Stress
          </th>

          <th className="text-left py-4">
            Burnout
          </th>

          <th className="text-left py-4">
            Sentiment
          </th>

        </tr>

      </thead>

      <tbody>

        {highRiskEmployees.map(
          (employee, index) => (

            <tr
              key={index}
              className="border-b"
            >

              <td className="py-4">
                {employee.name}
              </td>

              <td className="py-4">
                {employee.mood_score}
              </td>

              <td className="py-4">
                {employee.stress_level}
              </td>

              <td className="py-4">
                {employee.burnout_risk}
              </td>

              <td className="py-4">

                <span className="bg-red-100 text-red-700 px-3 py-1 rounded-full">

                  {employee.sentiment}

                </span>

              </td>

            </tr>

          )
        )}

      </tbody>

    </table>

  )}

</div>

    </div>
  );
}

export default ManagerDashboard;
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import API from "../services/api";

function Dashboard() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [aiInsight, setAiInsight] = useState(null);
  const [analytics, setAnalytics] = useState({
    average_mood: 0,
    average_stress: 0,
    average_burnout: 0,
    total_entries: 0,
  });

  const [chartData, setChartData] = useState([]);
  const [voiceStatus, setVoiceStatus] = useState(false);

  useEffect(() => {
    fetchAnalytics();
    fetchHistory();
    fetchAIInsight();
  }, []);
  useEffect(() => {
  checkVoiceStatus();
}, []);

const checkVoiceStatus = async () => {
  try {
    const userId = localStorage.getItem("user_id");

const response = await API.get(
  `/voice/status/${userId}`
);

    setVoiceStatus(
      response.data.completed_today
    );
  } catch (error) {
    console.log(error);
  }
};
 const fetchAnalytics = async () => {
  try {
    setLoading(true);

    const userId = localStorage.getItem("user_id");

    const response = await API.get(
      `/analytics/summary/${userId}`
    );

    setAnalytics(response.data);
  } catch (error) {
    console.error(error);
    alert("Failed to load analytics");
  } finally {
    setLoading(false);
  }
};
const fetchHistory = async () => {
  try {
    const userId =
      localStorage.getItem("user_id");

    const response = await API.get(
      `/wellness/history/${userId}`
    );

    const formattedData =
      response.data.map((entry) => ({
        date: new Date(
          entry.created_at
        ).toLocaleDateString(),

        mood: entry.mood_score,

        stress: entry.stress_level,

        burnout: entry.burnout_risk,
      }));

    setChartData(formattedData);

  } catch (error) {
    console.error(error);
  }
};
const fetchAIInsight = async () => {
  try {

    const userId =
      localStorage.getItem("user_id");

    const response = await API.get(
      `/analytics/ai-insight/${userId}`
    );

    setAiInsight(response.data);

  } catch (error) {

    console.error(error);

  }
};
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#FDFBD4]">
        <h1 className="text-3xl font-bold text-[#38240D]">
          Loading Dashboard...
        </h1>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FDFBD4]">
      
      {/* Main */}
      <div className="p-8">

        {/* Header */}
        <div className="flex justify-between items-center mb-10">

          <div>
            <h1 className="text-5xl font-bold text-[#38240D]">
  Employee Dashboard
</h1>

<p className="text-[#713600] mt-2">
  Welcome back, {localStorage.getItem("name")}
</p>
          </div>

          <div className="flex gap-3">

            <button
              onClick={fetchAnalytics}
              className="bg-[#713600] text-white px-5 py-3 rounded-xl"
            >
              Refresh
            </button>

          </div>

        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
              <div className="bg-white rounded-2xl p-6 shadow-md">
  <h3 className="font-bold text-xl">
    🎤 Voice Wellness Coach
  </h3>

  <p className="mt-2">
    {voiceStatus
      ? "Completed Today ✅"
      : "Pending ⚠️"}
  </p>
</div>
          <div className="bg-white rounded-3xl p-6 shadow-lg">
            <h2 className="text-[#713600] mb-2">
              Average Mood
            </h2>

            <p className="text-4xl font-bold text-[#38240D]">
              {Number(analytics.average_mood).toFixed(1)}
            </p>
          </div>

          <div className="bg-white rounded-3xl p-6 shadow-lg">
            <h2 className="text-[#713600] mb-2">
              Average Stress
            </h2>

            <p className="text-4xl font-bold text-[#38240D]">
              {Number(analytics.average_stress).toFixed(1)}
            </p>
          </div>

          <div className="bg-white rounded-3xl p-6 shadow-lg">
            <h2 className="text-[#713600] mb-2">
              Burnout Level
            </h2>

            <p className="text-4xl font-bold text-[#38240D]">
              {Number(analytics.average_burnout).toFixed(1)}
            </p>
          </div>

          <div className="bg-white rounded-3xl p-6 shadow-lg">
            <h2 className="text-[#713600] mb-2">
              Total Entries
            </h2>

            <p className="text-4xl font-bold text-[#38240D]">
              {analytics.total_entries}
            </p>
          </div>

        </div>
        <div className="bg-white rounded-3xl p-6 shadow-lg mb-8">

  <h2 className="text-xl font-bold text-[#38240D] mb-3">
    Wellness Status
  </h2>

  <p className="text-[#713600]">

    {analytics.average_stress >= 4
      ? "Stress levels are elevated. Consider taking breaks and reviewing workload balance."
      : "Your wellness indicators are currently within a healthy range."}

  </p>

</div>
        {/* AI Insight Card */}
{aiInsight && (
  <div className="bg-white rounded-3xl p-6 shadow-lg mb-8 border-l-8 border-[#C05800]">

    <h2 className="text-2xl font-bold text-[#38240D] mb-4">
      AI Wellness Insight
    </h2>

    <div className="space-y-4">

      <div className="flex items-center gap-2">
        <span className="font-semibold text-[#38240D]">
          Sentiment:
        </span>

        <span
          className={`px-3 py-1 rounded-full text-sm font-semibold ${
            aiInsight.sentiment === "Positive"
              ? "bg-green-100 text-green-700"
              : aiInsight.sentiment === "Negative"
              ? "bg-red-100 text-red-700"
              : "bg-yellow-100 text-yellow-700"
          }`}
        >
          {aiInsight.sentiment}
        </span>
      </div>

      <div className="p-4 rounded-xl bg-[#FDFBD4] text-[#38240D] leading-relaxed">
        <strong>Recommendation:</strong>
        <br />
        {aiInsight.recommendation}
      </div>

    </div>

  </div>
)}

        {/* Chart */}
        {/* Wellness Trends */}
<div className="bg-white rounded-3xl p-8 shadow-lg min-h-[500px]">

  <div className="flex justify-between items-center mb-8">

    <h2 className="text-3xl font-bold text-[#38240D]">
      Wellness Trends
    </h2>

    <span className="text-[#713600] font-medium">
      Last 7 Days
    </span>

  </div>

  {chartData.length === 0 ? (

    <div className="h-[350px] flex items-center justify-center text-[#713600]">
      No wellness data available
    </div>

  ) : (

    <ResponsiveContainer width="100%" height={400}>

      <LineChart
        data={chartData}
        margin={{
          top: 20,
          right: 30,
          left: 10,
          bottom: 20,
        }}
      >

        <XAxis
          dataKey="date"
        />

        <YAxis
          domain={[0, 10]}
        />

        <Tooltip />

        <Legend />

        <Line
          type="monotone"
          dataKey="mood"
          name="Mood"
          stroke="#C05800"
          strokeWidth={4}
          dot={{ r: 5 }}
          activeDot={{ r: 8 }}
        />

        <Line
          type="monotone"
          dataKey="stress"
          name="Stress"
          stroke="#713600"
          strokeWidth={4}
          dot={{ r: 5 }}
          activeDot={{ r: 8 }}
        />

        <Line
          type="monotone"
          dataKey="burnout"
          name="Burnout"
          stroke="#38240D"
          strokeWidth={4}
          dot={{ r: 5 }}
          activeDot={{ r: 8 }}
        />

      </LineChart>

    </ResponsiveContainer>

  )}

</div>

      </div>
    </div>
  );
}

export default Dashboard;
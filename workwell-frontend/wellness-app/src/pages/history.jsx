import { useEffect, useState } from "react";
import API from "../services/api";

function History() {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const userId =
        localStorage.getItem("user_id");

      const response = await API.get(
        `/wellness/history/${userId}`
      );

      console.log(response.data);

      setHistory(response.data);

    } catch (error) {
      console.error(error);
      alert("Failed to load history");
    }
  };

  return (
    <div className="min-h-screen bg-[#FDFBD4] p-8">

      <h1 className="text-5xl font-bold text-[#38240D] mb-8">
        Wellness History
      </h1>

      <div className="bg-white rounded-3xl shadow-lg overflow-hidden">

        <table className="w-full">

          <thead className="bg-[#38240D] text-white">

            <tr>
              <th className="p-4 text-left">Date</th>
              <th className="p-4 text-left">Mood</th>
              <th className="p-4 text-left">Stress</th>
              <th className="p-4 text-left">Burnout</th>
              <th className="p-4 text-left">Notes</th>
            </tr>

          </thead>

          <tbody>

            {history.map((entry) => (
              <tr
                key={entry.id}
                className="border-b"
              >
                <td className="p-4">
                  {new Date(
                    entry.created_at
                  ).toLocaleDateString()}
                </td>

                <td className="p-4">
                  {entry.mood_score}
                </td>

                <td className="p-4">
                  {entry.stress_level}
                </td>

                <td className="p-4">
                  {entry.burnout_risk}
                </td>

                <td className="p-4">
                  {entry.notes}
                </td>
              </tr>
            ))}

          </tbody>

        </table>

      </div>

    </div>
  );
}

export default History;
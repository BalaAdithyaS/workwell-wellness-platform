import { useEffect, useState } from "react";
import API from "../services/api";

function History() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);

      const userId =
        localStorage.getItem("user_id");

      const response = await API.get(
        `/wellness/unified-history/${userId}`
      );

      setHistory(response.data);
    } catch (error) {
      console.error(
        "Failed to load history:",
        error
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#FDFBD4] flex items-center justify-center">
        <p className="text-xl font-semibold text-[#38240D]">
          Loading wellness history...
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FDFBD4] p-8">

      <div className="max-w-7xl mx-auto">

        <div className="mb-8">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#C05800]">
            Your Wellness Journey
          </p>

          <h1 className="text-5xl font-bold text-[#38240D] mt-2">
            Wellness History
          </h1>

          <p className="text-[#713600] mt-3">
            Review your form submissions and voice wellness sessions.
          </p>
        </div>

        {history.length === 0 ? (

          <div className="bg-white rounded-3xl shadow-lg p-16 text-center">

            <h2 className="text-2xl font-bold text-[#38240D]">
              No wellness history yet
            </h2>

            <p className="text-[#713600] mt-3">
              Complete a wellness form or voice session to see your history here.
            </p>

          </div>

        ) : (

          <div className="space-y-4">

            {history.map((entry) => (

              <div
                key={`${entry.type}-${entry.id}`}
                className="bg-white rounded-3xl shadow-md p-6"
              >

                <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">

                  <div className="flex items-center gap-4">

                    <div
                      className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold ${
                        entry.type === "voice"
                          ? "bg-[#C05800] text-white"
                          : "bg-[#FFF8D6] text-[#38240D]"
                      }`}
                    >
                      {entry.type === "voice"
                        ? "V"
                        : "F"}
                    </div>

                    <div>
                      <div className="flex items-center gap-3">

                        <h2 className="text-xl font-bold text-[#38240D]">
                          {entry.type === "voice"
                            ? "Voice Wellness Session"
                            : "Wellness Form"}
                        </h2>

                        <span className="text-xs font-semibold uppercase tracking-wide bg-[#FFF8D6] text-[#713600] px-3 py-1 rounded-full">
                          {entry.type}
                        </span>

                      </div>

                      <p className="text-[#713600] mt-1">
                        {new Date(
                          entry.created_at
                        ).toLocaleString()}
                      </p>
                    </div>

                  </div>

                  <div className="flex flex-wrap gap-3">

                    {entry.type === "form" && (
                      <>
                        <div className="bg-[#FDFBD4] rounded-xl px-4 py-3">
                          <p className="text-xs text-[#713600]">
                            Mood
                          </p>

                          <p className="font-bold text-[#38240D]">
                            {entry.mood_score ?? "—"}
                          </p>
                        </div>

                        <div className="bg-[#FDFBD4] rounded-xl px-4 py-3">
                          <p className="text-xs text-[#713600]">
                            Stress
                          </p>

                          <p className="font-bold text-[#38240D]">
                            {entry.stress_level ?? "—"}
                          </p>
                        </div>
                      </>
                    )}

                    <div className="bg-[#FDFBD4] rounded-xl px-4 py-3">
                      <p className="text-xs text-[#713600]">
                        {entry.type === "voice"
                          ? "Risk"
                          : "Burnout"}
                      </p>

                      <p className="font-bold text-[#38240D]">
                        {entry.burnout_risk ?? "—"}
                      </p>
                    </div>

                    <div className="bg-[#FDFBD4] rounded-xl px-4 py-3">
                      <p className="text-xs text-[#713600]">
                        Sentiment
                      </p>

                      <p className="font-bold text-[#38240D]">
                        {entry.sentiment ?? "—"}
                      </p>
                    </div>

                  </div>

                </div>

                {entry.recommendation && (
                  <div className="mt-5 pt-5 border-t border-[#713600]/10">

                    <p className="text-sm font-semibold text-[#38240D]">
                      Recommendation
                    </p>

                    <p className="text-[#713600] mt-2 leading-relaxed">
                      {entry.recommendation}
                    </p>

                  </div>
                )}

              </div>

            ))}

          </div>
        )}

      </div>

    </div>
  );
}

export default History;
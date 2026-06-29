import { useState } from "react";
import API from "../services/api";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
function WellnessForm() {
  const moods = [
    { emoji: "😄", label: "Happy", score: 9 },
    { emoji: "🙂", label: "Good", score: 7 },
    { emoji: "😐", label: "Okay", score: 5 },
    { emoji: "😔", label: "Low", score: 3 },
    { emoji: "😣", label: "Burned Out", score: 1 },
  ];

  const [selectedMood, setSelectedMood] = useState("");
  const [stressLevel, setStressLevel] = useState(3);
  const [sleepHours, setSleepHours] = useState("");
  const [energyLevel, setEnergyLevel] = useState("Moderate");
  const [notes, setNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [aiResult, setAiResult] = useState(null);
  const navigate = useNavigate();
const handleSubmit = async (e) => {
  e.preventDefault();

  if (isSubmitting) return;

  if (!selectedMood) {
    toast.warning("Please select a mood");
    return;
  }

  setIsSubmitting(true);

  try {
    const moodData = moods.find(
      (m) => m.label === selectedMood
    );

    const userId = localStorage.getItem("user_id");

    if (!userId) {
      toast.error("User ID not found. Please login again.");
      return;
    }

    const payload = {
      user_id: userId,
      mood_score: moodData.score,
      stress_level: stressLevel,
      burnout_risk:
        stressLevel >= 5
          ? 4
          : stressLevel >= 3
          ? 2
          : 1,
      notes,
    };

    console.log("Submitting:", payload);

    // Submit ONLY ONCE
    const response = await API.post(
      "/wellness/submit",
      payload
    );

    console.log(response.data);

    // Optional AI analysis
    try {
      const aiResponse = await API.post(
        "/ai/analyze",
        {
          text: notes || selectedMood,
        }
      );

      setAiResult(aiResponse.data);

    } catch (err) {
      console.log("AI Analysis Failed", err);
    }

    // Reset form
    setSelectedMood("");
    setStressLevel(3);
    setSleepHours("");
    setEnergyLevel("Moderate");
    setNotes("");

    toast.success("Wellness Report Submitted Successfully");

    setTimeout(() => {
      navigate("/dashboard");
    }, 1000);

  } catch (error) {

    console.error(error);

    toast.error(
      error.response?.data?.detail ||
      "Failed to submit wellness report."
    );

  } finally {

    setIsSubmitting(false);

  }
};

console.log("AI RESULT:", aiResult);
  return (
    <div className="min-h-screen bg-[#FDFBD4] p-6 flex items-center justify-center">
      <div className="w-full max-w-4xl bg-white rounded-3xl shadow-xl p-8">

        <div className="mb-10">
          <h1 className="text-5xl font-bold text-[#38240D] mb-2">
            Wellness Check
          </h1>

          <p className="text-[#713600]">
            Track your daily mental and physical well-being.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">

          {/* Mood */}
          <div>
            <label className="block mb-4 font-semibold text-[#713600] text-lg">
              How are you feeling today?
            </label>

            <div className="grid grid-cols-2 sm:grid-cols-5 gap-4">

              {moods.map((mood) => (
                <button
                  key={mood.label}
                  type="button"
                  onClick={() => setSelectedMood(mood.label)}
                  className={`p-5 rounded-2xl border transition-all duration-300 flex flex-col items-center ${
                    selectedMood === mood.label
                      ? "bg-[#C05800] text-white scale-105 shadow-lg"
                      : "bg-[#FDFBD4] text-[#38240D] hover:bg-[#C05800] hover:text-white"
                  }`}
                >
                  <span className="text-4xl mb-3">
                    {mood.emoji}
                  </span>

                  <span className="font-medium">
                    {mood.label}
                  </span>
                </button>
              ))}

            </div>
          </div>

          {/* Stress */}
          <div>
            <label className="block mb-4 font-semibold text-[#713600] text-lg">
              Stress Level: {stressLevel}
            </label>

            <input
              type="range"
              min="1"
              max="6"
              step="1"
              value={stressLevel}
              onChange={(e) =>
                setStressLevel(Number(e.target.value))
              }
              className="w-full accent-[#C05800]"
            />

            <div className="flex justify-between text-[#713600] text-sm mt-2">
              <span>1</span>
              <span>2</span>
              <span>3</span>
              <span>4</span>
              <span>5</span>
              <span>6</span>
            </div>

            <div className="flex justify-between text-xs text-[#713600] mt-1">
              <span>Very Low</span>
              <span></span>
              <span>Moderate</span>
              <span></span>
              <span></span>
              <span>Extreme</span>
            </div>
          </div>

          {/* Sleep */}
          <div>
            <label className="block mb-3 font-semibold text-[#713600] text-lg">
              Sleep Hours
            </label>

            <input
              type="number"
              value={sleepHours}
              onChange={(e) =>
                setSleepHours(e.target.value)
              }
              placeholder="Enter sleep duration"
              className="w-full p-4 rounded-2xl border border-[#713600]/20 focus:outline-none focus:ring-2 focus:ring-[#C05800]"
            />
          </div>

          {/* Energy */}
          <div>
            <label className="block mb-3 font-semibold text-[#713600] text-lg">
              Energy Level
            </label>

            <select
              value={energyLevel}
              onChange={(e) =>
                setEnergyLevel(e.target.value)
              }
              className="w-full p-4 rounded-2xl border border-[#713600]/20 focus:outline-none focus:ring-2 focus:ring-[#C05800]"
            >
              <option>Very Low</option>
              <option>Low</option>
              <option>Moderate</option>
              <option>High</option>
              <option>Very High</option>
            </select>
          </div>

          {/* Notes */}
          <div>
            <label className="block mb-3 font-semibold text-[#713600] text-lg">
              Additional Notes
            </label>

            <textarea
              value={notes}
              onChange={(e) =>
                setNotes(e.target.value)
              }
              placeholder="Write anything about your day..."
              className="w-full p-4 rounded-2xl border border-[#713600]/20 h-36 focus:outline-none focus:ring-2 focus:ring-[#C05800]"
            />
          </div>

          {/* Submit */}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-[#C05800] hover:bg-[#713600] text-white py-4 rounded-2xl text-lg font-semibold transition-all duration-300 shadow-md hover:shadow-xl disabled:opacity-50"
          >
            {isSubmitting
              ? "Submitting..."
              : "Submit Wellness Report"}
          </button>
          
        </form>
      </div>
    </div>
  );
}

export default WellnessForm;
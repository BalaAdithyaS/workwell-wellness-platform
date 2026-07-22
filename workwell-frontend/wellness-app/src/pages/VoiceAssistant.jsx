import { useEffect, useRef, useState } from "react";
import API from "../services/api";

const GREETING =
  "Hi there! I'm your wellness coach. I'd love to hear how you're doing — what's been on your mind lately?";

function VoiceAssistant() {
  const [conversation, setConversation] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState(GREETING);
  const [answer, setAnswer] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [status, setStatus] = useState("ready");
  const [error, setError] = useState("");

  const recognitionRef = useRef(null);
  const conversationRef = useRef([]);
  const stoppedRef = useRef(false);
  const selectedVoiceRef = useRef(null);

  useEffect(() => {
    stoppedRef.current = false;
    loadPreferredVoice().then(() => setStatus("ready"));

    return () => {
      stoppedRef.current = true;
      if (recognitionRef.current) recognitionRef.current.abort();
      window.speechSynthesis.cancel();
    };
  }, []);

  const loadPreferredVoice = () =>
    new Promise((resolve) => {
      const findVoice = () => {
        const voices = window.speechSynthesis.getVoices();
        if (voices.length === 0) return false;
        selectedVoiceRef.current =
          voices.find((v) => v.name.includes("Microsoft Aria")) ||
          voices.find((v) => v.name.includes("Zira")) ||
          voices.find((v) => v.name.includes("Google UK English Female")) ||
          voices.find(
            (v) => v.lang.startsWith("en") && v.name.toLowerCase().includes("female"),
          ) ||
          voices.find((v) => v.lang.startsWith("en"));
        resolve(selectedVoiceRef.current);
        return true;
      };
      if (findVoice()) return;
      window.speechSynthesis.onvoiceschanged = () => findVoice();
    });

  const speak = (text) =>
    new Promise((resolve) => {
      if (stoppedRef.current) { resolve(); return; }
      setStatus("speaking");
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      if (selectedVoiceRef.current) utter.voice = selectedVoiceRef.current;
      utter.rate = 0.95;
      utter.pitch = 1.05;
      utter.onend = () => resolve();
      utter.onerror = () => resolve();
      window.speechSynthesis.speak(utter);
    });

  const startListening = () => {
    if (stoppedRef.current) return;
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setStatus("error");
      setError("Voice recognition is not supported in this browser. Please use Chrome or Edge.");
      return;
    }
    if (recognitionRef.current) recognitionRef.current.abort();

    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognitionRef.current = recognition;

    let finalTranscript = "";

    recognition.onstart = () => {
      setAnswer("");
      setError("");
      setStatus("listening");
    };

    recognition.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalTranscript += t;
        else interim += t;
      }
      setAnswer(finalTranscript || interim);
    };

    recognition.onspeechend = () => recognition.stop();

    recognition.onend = () => {
      recognitionRef.current = null;
      const clean = finalTranscript.trim();
      if (clean && !stoppedRef.current) handleAnswer(clean);
      else if (!stoppedRef.current) setStatus("ready");
    };

    recognition.onerror = (event) => {
      recognitionRef.current = null;
      if (event.error === "no-speech" || event.error === "aborted") {
        setStatus("ready");
        return;
      }
      setStatus("error");
      setError("I couldn't hear that clearly. Tap the mic and try again.");
    };

    try { recognition.start(); } catch { setStatus("ready"); }
  };

  const handleAnswer = async (spokenAnswer) => {
    if (!spokenAnswer || stoppedRef.current) return;
    setStatus("processing");

    const updatedConv = [
      ...conversationRef.current,
      { role: "coach", content: currentQuestion },
      { role: "user", content: spokenAnswer },
    ];
    conversationRef.current = updatedConv;
    setConversation(
      updatedConv.map((m) => ({
        who: m.role === "coach" ? "coach" : "you",
        text: m.content,
      })),
    );
    setAnswer(spokenAnswer);

    try {
      const { data } = await API.post("/voice/chat", {
        conversation: updatedConv,
      });

      if (data.done || !data.next_question) {
        await completeAssessment(updatedConv);
        return;
      }

      setCurrentQuestion(data.next_question);
      setAnswer("");
      await speak(data.next_question);
      startListening();
    } catch (err) {
      console.error("Chat error:", err);
      const msg =
        err.response?.data?.detail || err.message || "Unknown error";
      if (
        msg.toLowerCase().includes("quota") ||
        msg.toLowerCase().includes("unavailable") ||
        err.response?.status === 503
      ) {
        setStatus("error");
        setError(
          "AI coaching is temporarily unavailable because the Gemini API quota has been reached. You can finish your session now with what you have shared.",
        );
        if (conversationRef.current.length >= 2) {
          await completeAssessment(conversationRef.current);
        }
      } else {
        setStatus("error");
        setError(`Could not continue: ${msg}. Tap the mic to try again.`);
      }
    }
  };

  const completeAssessment = async (finalConversation) => {
    try {
      setStatus("processing");
      setError("");

      const transcriptText = finalConversation
        .map((m) => `${m.role === "coach" ? "Coach" : "User"}: ${m.content}`)
        .join("\n\n");

      const { data } = await API.post("/voice/analyze", {
        conversation: transcriptText,
      });

      setAnalysis({
        sentiment: data.sentiment,
        recommendation: data.recommendation,
        mood_score: data.mood_score,
        stress_level: data.stress_level,
        burnout_risk: data.burnout_risk,
        sleep_hours: data.sleep_hours,
        energy_level: data.energy_level,
      });
      setStatus("completed");
      window.speechSynthesis.cancel();
    } catch (err) {
      console.error("Analysis error:", err);
      const detail = err.response?.data?.detail || err.message || "";
      setStatus("error");
      if (
        detail.toLowerCase().includes("quota") ||
        err.response?.status === 503
      ) {
        setError(
          "AI analysis is temporarily unavailable because the Gemini API quota has been reached. Your conversation has been saved.",
        );
      } else {
        setError(`Unable to generate your wellness report: ${detail}`);
      }
    }
  };

  const finishConversation = () => {
    if (conversationRef.current.length === 0) {
      setError("Complete at least one response first.");
      return;
    }
    if (recognitionRef.current) {
      recognitionRef.current.abort();
      recognitionRef.current = null;
    }
    window.speechSynthesis.cancel();
    completeAssessment(conversationRef.current);
  };

  const statusText = {
    ready: "Ready when you are",
    speaking: "Coach is speaking",
    listening: "Listening to you",
    processing: "Understanding your response",
    completed: "Assessment complete",
    error: "Something went wrong",
  };

  const turnCount = Math.floor(conversation.length / 2);

  return (
    <div className="min-h-screen bg-[#FDFBD4] px-6 py-10">
      <div className="max-w-6xl mx-auto">
        {!analysis ? (
          <div className="grid lg:grid-cols-[1fr_380px] gap-8">
            {/* Main Conversation Area */}
            <div className="bg-white rounded-[32px] shadow-lg p-8 lg:p-12 min-h-[700px] flex flex-col">
              <div className="mb-10">
                <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[#C05800]">
                  Private Wellness Session
                </p>
                <h1 className="text-4xl lg:text-5xl font-bold text-[#38240D] mt-3">
                  AI Wellness Coach
                </h1>
                <p className="text-[#713600] mt-3">
                  A natural voice conversation about how you're doing.
                </p>
              </div>

              <div className="flex-1 flex flex-col items-center justify-center text-center">
                <div className="relative flex items-center justify-center mb-10">
                  {status === "listening" && (
                    <>
                      <div className="absolute w-48 h-48 rounded-full bg-[#C05800]/10 animate-ping" />
                      <div className="absolute w-36 h-36 rounded-full bg-[#C05800]/20 animate-pulse" />
                    </>
                  )}
                  {status === "speaking" && (
                    <div className="absolute w-44 h-44 rounded-full bg-[#713600]/10 animate-pulse" />
                  )}
                  <button
                    onClick={() => {
                      if (status === "ready" || status === "error") {
                        speak(currentQuestion).then(() => startListening());
                      }
                    }}
                    disabled={status === "processing" || status === "speaking"}
                    className={`relative z-10 w-32 h-32 rounded-full flex items-center justify-center text-4xl shadow-xl transition-all duration-500 ${
                      status === "listening"
                        ? "bg-[#C05800] text-white scale-110"
                        : status === "processing"
                          ? "bg-[#38240D] text-white"
                          : status === "speaking"
                            ? "bg-[#713600] text-white"
                            : "bg-[#C05800] text-white hover:scale-105"
                    }`}
                  >
                    {status === "processing" ? "..." : status === "speaking" ? "◖" : "●"}
                  </button>
                </div>

                <p className="text-sm uppercase tracking-[0.18em] font-semibold text-[#C05800]">
                  {statusText[status]}
                </p>

                <h2 className="text-3xl lg:text-4xl font-semibold text-[#38240D] max-w-3xl mt-5 leading-tight">
                  {currentQuestion}
                </h2>

                <div className="mt-10 min-h-[90px] max-w-2xl w-full">
                  {answer ? (
                    <div className="bg-[#FFF8D6] rounded-2xl px-6 py-5 text-[#38240D] text-lg">
                      &ldquo;{answer}&rdquo;
                    </div>
                  ) : (
                    <p className="text-gray-400">
                      {status === "listening"
                        ? "Speak naturally. I'll detect when you're finished."
                        : "Your response will appear here."}
                    </p>
                  )}
                </div>

                {error && (
                  <div className="mt-6 bg-red-50 text-red-700 rounded-2xl px-5 py-4 max-w-2xl">
                    {error}
                  </div>
                )}

                {status === "ready" && (
                  <button
                    onClick={() =>
                      speak(currentQuestion).then(() => startListening())
                    }
                    className="mt-6 px-7 py-3 rounded-xl bg-[#C05800] text-white font-semibold hover:bg-[#713600] transition"
                  >
                    Speak Again
                  </button>
                )}
              </div>
            </div>

            {/* Session Panel */}
            <div className="space-y-6">
              <div className="bg-[#38240D] text-white rounded-[32px] p-8">
                <p className="text-sm text-gray-300">Session Progress</p>
                <p className="text-5xl font-bold mt-3">{turnCount}</p>
                <p className="text-gray-300 mt-2">responses completed</p>
                <div className="h-2 bg-white/10 rounded-full mt-6 overflow-hidden">
                  <div
                    className="h-full bg-[#C05800] rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min((turnCount / 5) * 100, 100)}%`,
                    }}
                  />
                </div>
              </div>

              <div className="bg-white rounded-[32px] shadow-lg p-7">
                <h3 className="text-xl font-bold text-[#38240D]">How it works</h3>
                <div className="mt-6 space-y-5 text-[#713600]">
                  <p>The coach listens to your responses.</p>
                  <p>Each follow-up question adapts to what you shared.</p>
                  <p>When enough information is gathered, your wellness report is generated.</p>
                </div>
              </div>

              {turnCount > 0 && (
                <button
                  onClick={finishConversation}
                  disabled={status === "processing"}
                  className="w-full bg-white border-2 border-[#C05800] text-[#C05800] rounded-2xl py-4 font-semibold hover:bg-[#C05800] hover:text-white transition"
                >
                  Finish Session
                </button>
              )}
            </div>
          </div>
        ) : (
          /* Final Report */
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-[32px] shadow-xl overflow-hidden">
              <div className="bg-[#38240D] text-white p-10">
                <p className="text-[#FDFBD4] uppercase tracking-[0.2em] text-sm">
                  Session Complete
                </p>
                <h1 className="text-4xl font-bold mt-3">Your Wellness Report</h1>
              </div>

              <div className="p-10">
                <div className="grid md:grid-cols-2 gap-6">
                  <div className="bg-[#FFF8D6] rounded-3xl p-7">
                    <p className="text-[#713600]">Mood Score</p>
                    <p className="text-3xl font-bold text-[#38240D] mt-2">
                      {analysis.mood_score}/10
                    </p>
                  </div>
                  <div className="bg-[#FFF8D6] rounded-3xl p-7">
                    <p className="text-[#713600]">Stress Level</p>
                    <p className="text-3xl font-bold text-[#38240D] mt-2">
                      {analysis.stress_level}/10
                    </p>
                  </div>
                  <div className="bg-[#FFF8D6] rounded-3xl p-7">
                    <p className="text-[#713600]">Sentiment</p>
                    <p className="text-3xl font-bold text-[#38240D] mt-2 capitalize">
                      {analysis.sentiment}
                    </p>
                  </div>
                  <div className="bg-[#FFF8D6] rounded-3xl p-7">
                    <p className="text-[#713600]">Burnout Risk</p>
                    <p className="text-3xl font-bold text-[#38240D] mt-2">
                      {analysis.burnout_risk}/10
                    </p>
                  </div>
                  {analysis.sleep_hours != null && (
                    <div className="bg-[#FFF8D6] rounded-3xl p-7">
                      <p className="text-[#713600]">Sleep Hours</p>
                      <p className="text-3xl font-bold text-[#38240D] mt-2">
                        {analysis.sleep_hours}h
                      </p>
                    </div>
                  )}
                  {analysis.energy_level && (
                    <div className="bg-[#FFF8D6] rounded-3xl p-7">
                      <p className="text-[#713600]">Energy Level</p>
                      <p className="text-3xl font-bold text-[#38240D] mt-2">
                        {analysis.energy_level}
                      </p>
                    </div>
                  )}
                </div>

                <div className="mt-6 bg-[#FDFBD4] rounded-3xl p-8">
                  <h2 className="text-2xl font-bold text-[#38240D]">
                    Personal Recommendation
                  </h2>
                  <p className="text-[#713600] leading-relaxed mt-4 text-lg">
                    {analysis.recommendation}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default VoiceAssistant;

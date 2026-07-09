import { useEffect, useRef, useState } from "react";
import API from "../services/api";

function VoiceAssistant() {
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [conversation, setConversation] = useState([]);
  const [analysis, setAnalysis] = useState(null);

  const [status, setStatus] = useState("starting");
  const [error, setError] = useState("");

  const recognitionRef = useRef(null);
  const conversationRef = useRef([]);
  const currentQuestionRef = useRef("");
  const stoppedRef = useRef(false);
  const selectedVoiceRef = useRef(null);
  useEffect(() => {
  stoppedRef.current = false;
  startConversation();

  return () => {
    stoppedRef.current = true;

    if (recognitionRef.current) {
      recognitionRef.current.abort();
    }

    window.speechSynthesis.cancel();
  };
}, []);

const loadPreferredVoice = () => {
  return new Promise((resolve) => {
    const findVoice = () => {
      const voices = window.speechSynthesis.getVoices();

      if (voices.length === 0) {
        return false;
      }

      const preferredVoice =
        voices.find((voice) =>
          voice.name.includes("Microsoft Aria")
        ) ||
        voices.find((voice) =>
          voice.name.includes("Zira")
        ) ||
        voices.find((voice) =>
          voice.name.includes("Google UK English Female")
        ) ||
        voices.find(
          (voice) =>
            voice.lang.startsWith("en") &&
            voice.name.toLowerCase().includes("female")
        ) ||
        voices.find((voice) =>
          voice.lang.startsWith("en")
        );

      selectedVoiceRef.current = preferredVoice;

      console.log(
        "Locked voice:",
        preferredVoice?.name
      );

      resolve(preferredVoice);

      return true;
    };

    if (findVoice()) return;

    window.speechSynthesis.onvoiceschanged = () => {
      findVoice();
    };
  });
};


const startConversation = async () => {
  try {
    setStatus("starting");
    setError("");

    await loadPreferredVoice();

    const response = await API.get("/voice/start");

    const question = response.data.question;

    setCurrentQuestion(question);
    currentQuestionRef.current = question;

    setStatus("ready");
  } catch (error) {
    console.error(error);

    setStatus("error");

    setError(
      "Unable to start the wellness conversation."
    );
  }
};
  const speakQuestion = (question) => {
    if (stoppedRef.current) return;

    setStatus("speaking");

    window.speechSynthesis.cancel();

    const speech = new SpeechSynthesisUtterance(question);

    if (selectedVoiceRef.current) {
      speech.voice = selectedVoiceRef.current;
    }

    speech.rate = 0.95;
    speech.pitch = 1.05;

    speech.onend = () => {
      if (!stoppedRef.current) {
        setTimeout(() => {
          startListening();
        }, 400);
      }
    };

    speech.onerror = () => {
      if (!stoppedRef.current) {
        startListening();
      }
    };

    window.speechSynthesis.speak(speech);
  };

  const startListening = () => {
    if (stoppedRef.current) return;

    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setStatus("error");
      setError(
        "Voice recognition is not supported in this browser. Please use Chrome or Edge."
      );
      return;
    }

    if (recognitionRef.current) {
      recognitionRef.current.abort();
    }

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
      let interimTranscript = "";

      for (
        let i = event.resultIndex;
        i < event.results.length;
        i++
      ) {
        const transcript =
          event.results[i][0].transcript;

        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      setAnswer(
        finalTranscript || interimTranscript
      );
    };

    recognition.onspeechend = () => {
      recognition.stop();
    };

    recognition.onend = () => {
      recognitionRef.current = null;

      const cleanAnswer = finalTranscript.trim();

      if (cleanAnswer && !stoppedRef.current) {
        submitAnswer(cleanAnswer);
      } else if (!stoppedRef.current) {
        setStatus("ready");
      }
    };

    recognition.onerror = (event) => {
      recognitionRef.current = null;

      if (
        event.error === "no-speech" ||
        event.error === "aborted"
      ) {
        setStatus("ready");
        return;
      }

      console.error("Speech recognition error:", event.error);

      setStatus("error");
      setError(
        "I couldn't hear that clearly. Tap the voice button and try again."
      );
    };

    try {
      recognition.start();
    } catch (error) {
      console.error(error);
      setStatus("ready");
    }
  };

  const submitAnswer = async (spokenAnswer) => {
    if (!spokenAnswer || stoppedRef.current) return;

    setStatus("processing");

    const updatedConversation = [
      ...conversationRef.current,
      {
        question: currentQuestionRef.current,
        answer: spokenAnswer,
      },
    ];

    conversationRef.current = updatedConversation;

    setConversation(updatedConversation);
    setAnswer(spokenAnswer);

    try {
      const response = await API.post(
        "/voice/next-question",
        {
          conversation: updatedConversation,
        }
      );

      if (response.data.done) {
        await completeAssessment(
          updatedConversation
        );
        return;
      }

      const nextQuestion = response.data.question;

      setAnswer("");
      setCurrentQuestion(nextQuestion);

      currentQuestionRef.current = nextQuestion;

      speakQuestion(nextQuestion);
    } catch (error) {
      console.error(
        "Next Question Error:",
        error
      );

      setStatus("error");
      setError(
        "Something went wrong while processing your response."
      );
    }
  };

  const completeAssessment = async (
    finalConversation
  ) => {
    try {
      setStatus("processing");

      const userId =
        localStorage.getItem("user_id");

      const response = await API.post(
        "/voice/final-analysis",
        {
          user_id: userId,
          conversation: finalConversation,
        }
      );

      const parsed =
        typeof response.data.analysis === "string"
          ? JSON.parse(response.data.analysis)
          : response.data.analysis;

      setAnalysis(parsed);
      setStatus("completed");

      window.speechSynthesis.cancel();
    } catch (error) {
      console.error(
        "Final Analysis Error:",
        error
      );

      setStatus("error");
      setError(
        "Unable to generate your wellness report."
      );
    }
  };

  const finishConversation = async () => {
    if (conversationRef.current.length === 0) {
      setError(
        "Complete at least one response first."
      );
      return;
    }

    if (recognitionRef.current) {
      recognitionRef.current.abort();
      recognitionRef.current = null;
    }

    window.speechSynthesis.cancel();

    await completeAssessment(
      conversationRef.current
    );
  };

  const statusText = {
    starting: "Preparing your session",
    speaking: "Coach is speaking",
    listening: "Listening to you",
    processing: "Understanding your response",
    ready: "Ready when you are",
    completed: "Assessment complete",
    error: "Something went wrong",
  };

  return (
    <div className="min-h-screen bg-[#FDFBD4] px-6 py-10">

      <div className="max-w-6xl mx-auto">

        {!analysis ? (
          <div className="grid lg:grid-cols-[1fr_380px] gap-8">

            {/* Main Conversation Area */}
            <div className="bg-white rounded-[32px] shadow-lg p-8 lg:p-12 min-h-[700px] flex flex-col">

              {/* Header */}
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

              {/* Voice Experience */}
              <div className="flex-1 flex flex-col items-center justify-center text-center">

                {/* Voice Orb */}
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
                          speakQuestion(currentQuestionRef.current);
                        }
                    }}
                    disabled={
                      status === "processing" ||
                      status === "speaking" ||
                      status === "starting"
                    }
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
                    {status === "processing"
                      ? "•••"
                      : status === "speaking"
                      ? "◖"
                      : "●"}
                  </button>

                </div>

                {/* Status */}
                <p className="text-sm uppercase tracking-[0.18em] font-semibold text-[#C05800]">
                  {statusText[status]}
                </p>

                {/* Current Question */}
                <h2 className="text-3xl lg:text-4xl font-semibold text-[#38240D] max-w-3xl mt-5 leading-tight">
                  {currentQuestion ||
                    "Starting your conversation..."}
                </h2>

                {/* Live Transcript */}
                <div className="mt-10 min-h-[90px] max-w-2xl w-full">

                  {answer ? (
                    <div className="bg-[#FFF8D6] rounded-2xl px-6 py-5 text-[#38240D] text-lg">
                      “{answer}”
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
                  <div className="mt-6 bg-red-50 text-red-700 rounded-2xl px-5 py-4">
                    {error}
                  </div>
                )}

                {status === "ready" && (
                  <button
                    onClick={() => speakQuestion(currentQuestionRef.current)}
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

                <p className="text-sm text-gray-300">
                  Session Progress
                </p>

                <p className="text-5xl font-bold mt-3">
                  {conversation.length}
                </p>

                <p className="text-gray-300 mt-2">
                  responses completed
                </p>

                <div className="h-2 bg-white/10 rounded-full mt-6 overflow-hidden">
                  <div
                    className="h-full bg-[#C05800] rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(
                        conversation.length * 20,
                        100
                      )}%`,
                    }}
                  />
                </div>

              </div>

              <div className="bg-white rounded-[32px] shadow-lg p-7">

                <h3 className="text-xl font-bold text-[#38240D]">
                  How it works
                </h3>

                <div className="mt-6 space-y-5 text-[#713600]">

                  <p>
                    The coach asks you a question aloud.
                  </p>

                  <p>
                    Your microphone opens automatically.
                  </p>

                  <p>
                    When you stop speaking, your answer is sent automatically.
                  </p>

                </div>

              </div>

              {conversation.length > 0 && (
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

                <h1 className="text-4xl font-bold mt-3">
                  Your Wellness Report
                </h1>

              </div>

              <div className="p-10">

                <div className="grid md:grid-cols-2 gap-6">

                  <div className="bg-[#FFF8D6] rounded-3xl p-7">
                    <p className="text-[#713600]">
                      Sentiment
                    </p>

                    <p className="text-3xl font-bold text-[#38240D] mt-2">
                      {analysis.sentiment}
                    </p>
                  </div>

                  <div className="bg-[#FFF8D6] rounded-3xl p-7">
                    <p className="text-[#713600]">
                      Risk Level
                    </p>

                    <p className="text-3xl font-bold text-[#38240D] mt-2">
                      {analysis.risk_level}
                    </p>
                  </div>

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
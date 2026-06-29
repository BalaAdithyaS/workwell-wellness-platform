import { useEffect, useState } from "react";
import API from "../services/api";

function VoiceAssistant() {
  const [currentQuestion, setCurrentQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [conversation, setConversation] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    startConversation();
  }, []);

  const startConversation = async () => {
    try {
      const response = await API.get("/voice/start");

      setCurrentQuestion(response.data.question);

      speakQuestion(response.data.question);
    } catch (error) {
      console.log(error);
    }
  };

  const speakQuestion = (question) => {
    window.speechSynthesis.cancel();

    const speech =
      new SpeechSynthesisUtterance(question);

    const voices =
      window.speechSynthesis.getVoices();

    const femaleVoice =
      voices.find(
        (voice) =>
          voice.name.includes("Zira") ||
          voice.name.includes(
            "Google UK English Female"
          )
      );

    if (femaleVoice) {
      speech.voice = femaleVoice;
    }

    speech.rate = 0.95;
    speech.pitch = 1.05;

    window.speechSynthesis.speak(speech);
  };

  const startListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      alert(
        "Speech Recognition not supported"
      );
      return;
    }

    const recognition =
      new SpeechRecognition();

    recognition.lang = "en-US";
    recognition.interimResults = false;

    setIsListening(true);

    recognition.start();

    recognition.onresult = (event) => {
      const text =
        event.results[0][0].transcript;

      setAnswer(text);

      setIsListening(false);
    };

    recognition.onerror = () => {
      setIsListening(false);
    };
  };

const nextQuestion = async () => {

  if (!answer) {
    alert("Please answer first");
    return;
  }

  const updatedConversation = [
    ...conversation,
    {
      question: currentQuestion,
      answer: answer,
    },
  ];

  setConversation(updatedConversation);
  setAnswer("");

  try {

    const response = await API.post(
      "/voice/next-question",
      {
        conversation: updatedConversation,
      }
    );

    if (response.data.done) {

      const userId = localStorage.getItem("user_id");

      const finalResponse = await API.post(
        "/voice/final-analysis",
        {
          user_id: userId,
          conversation: updatedConversation,
        }
      );

      const parsed = JSON.parse(
        finalResponse.data.analysis
      );

      setAnalysis(parsed);

      return;
    }

    const nextQ = response.data.question;

    setCurrentQuestion(nextQ);

    speakQuestion(nextQ);

  } catch (error) {

    console.error("Next Question Error:", error);

  }

};
  return (
    <div className="min-h-screen bg-[#FDFBD4] flex justify-center py-10 px-4">

      <div className="w-full max-w-5xl">

        <div className="bg-white rounded-3xl shadow-xl overflow-hidden">

          <div className="bg-[#C05800] p-8 text-white">

            <h1 className="text-4xl font-bold">
              AI Wellness Coach
            </h1>

            <p className="mt-2 opacity-90">
              Voice-powered employee
              wellness assessment
            </p>

          </div>

          {!analysis ? (
            <div className="p-8">

              <div className="mb-8">

                <div className="flex justify-between mb-2">

                  <span className="font-semibold">
                    Progress
                  </span>

                  <span>
                    {
                      conversation.length
                    }{" "}
                    Responses
                  </span>

                </div>

                <div className="h-3 bg-gray-200 rounded-full">

                  <div
                    className="h-3 bg-[#C05800] rounded-full transition-all duration-500"
                    style={{
                      width: `${Math.min(
                        conversation.length *
                          20,
                        100
                      )}%`,
                    }}
                  />

                </div>

              </div>

              <div className="space-y-4 max-h-[450px] overflow-y-auto">

                {conversation.map(
                  (
                    item,
                    index
                  ) => (
                    <div
                      key={index}
                    >

                      <div className="bg-[#FFF8D6] p-4 rounded-2xl w-fit max-w-[80%]">

                        🤖{" "}
                        {
                          item.question
                        }

                      </div>

                      <div className="bg-[#C05800] text-white p-4 rounded-2xl ml-auto mt-3 w-fit max-w-[80%]">

                        🎤{" "}
                        {
                          item.answer
                        }

                      </div>

                    </div>
                  )
                )}

                <div className="bg-[#FFF8D6] p-5 rounded-2xl max-w-[80%]">

                  <p className="font-semibold mb-2">
                    AI Question
                  </p>

                  <p>
                    {
                      currentQuestion
                    }
                  </p>

                </div>

              </div>

              <div className="mt-8 bg-gray-100 rounded-2xl p-5">

                <h3 className="font-bold mb-3">
                  Your Response
                </h3>

                <p className="min-h-[60px] text-lg">

                  {answer ||
                    "Tap the microphone and answer..."}

                </p>

              </div>

              <div className="flex flex-wrap gap-4 mt-8">

                <button
                  onClick={
                    startListening
                  }
                  className="bg-[#C05800] hover:bg-[#713600] text-white px-6 py-3 rounded-xl font-semibold"
                >

                  {isListening
                    ? "🎙 Listening..."
                    : "🎤 Answer"}

                </button>

                <button
                  onClick={
                    nextQuestion
                  }
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-xl font-semibold"
                >
                  Next Question
                </button>

                <button
                  onClick={
                    finishConversation
                  }
                  className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-xl font-semibold"
                >
                  Finish Assessment
                </button>

              </div>

            </div>
          ) : (
            <div className="p-8">

              <h2 className="text-3xl font-bold mb-6 text-[#38240D]">
                Wellness Report
              </h2>

              <div className="grid md:grid-cols-2 gap-4 mb-6">

                <div className="bg-gray-100 rounded-2xl p-6">

                  <h3 className="font-semibold text-gray-500">
                    Sentiment
                  </h3>

                  <p className="text-2xl font-bold mt-2">
                    {
                      analysis.sentiment
                    }
                  </p>

                </div>

                <div className="bg-gray-100 rounded-2xl p-6">

                  <h3 className="font-semibold text-gray-500">
                    Risk Level
                  </h3>

                  <p className="text-2xl font-bold mt-2">
                    {
                      analysis.risk_level
                    }
                  </p>

                </div>

              </div>

              <div className="bg-[#FFF8D6] rounded-2xl p-6">

                <h3 className="text-xl font-bold mb-3">
                  Recommendation
                </h3>

                <p className="leading-relaxed">
                  {
                    analysis.recommendation
                  }
                </p>

              </div>

            </div>
          )}

        </div>

      </div>

    </div>
  );
}

export default VoiceAssistant;
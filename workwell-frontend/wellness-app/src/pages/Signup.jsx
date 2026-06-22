import { useState } from "react";
import { useNavigate } from "react-router-dom";
import API from "../services/api";

function Signup() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
  });

  const [isLoading, setIsLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSignup = async (e) => {
    e.preventDefault();

    try {
      setIsLoading(true);

const response = await API.post(
  "/auth/signup",
  formData
);

alert(JSON.stringify(response.data));
console.log(response.data);

      // Store user_id from backend response
      localStorage.setItem(
        "user_id",
        response.data.user_id
      );

      alert("Signup Successful");

      navigate("/");

    } catch (error) {
      console.error(error);

      alert(
        error.response?.data?.detail ||
        "Signup Failed"
      );

    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#FDFBD4] p-6">

      <form
        onSubmit={handleSignup}
        className="bg-white p-8 rounded-3xl shadow-xl w-full max-w-md"
      >

        <h1 className="text-4xl font-bold mb-2 text-[#38240D]">
          Create Account
        </h1>

        <p className="text-[#713600] mb-6">
          Join WorkWell and start tracking wellness.
        </p>

        <input
          type="text"
          name="name"
          placeholder="Full Name"
          value={formData.name}
          onChange={handleChange}
          className="w-full p-4 mb-4 border border-[#713600]/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#C05800]"
          required
        />

        <input
          type="email"
          name="email"
          placeholder="Email Address"
          value={formData.email}
          onChange={handleChange}
          className="w-full p-4 mb-4 border border-[#713600]/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#C05800]"
          required
        />

        <input
          type="password"
          name="password"
          placeholder="Password"
          value={formData.password}
          onChange={handleChange}
          className="w-full p-4 mb-6 border border-[#713600]/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#C05800]"
          required
        />

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-[#C05800] hover:bg-[#713600] text-white p-4 rounded-xl font-semibold transition-all"
        >
          {isLoading ? "Creating Account..." : "Signup"}
        </button>

      </form>

    </div>
  );
}

export default Signup;
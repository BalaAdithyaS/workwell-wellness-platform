import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import API from "../services/api";

function Signup() {
  const navigate = useNavigate();

const [formData, setFormData] = useState({
  name: "",
  email: "",
  password: "",
  team_id: "",
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

    if (isLoading) return;

    try {
      setIsLoading(true);

      const response = await API.post(
        "/auth/signup",
        formData
      );

      localStorage.setItem(
        "user_id",
        response.data.user_id
      );

      toast.success("Account created successfully!");

      setTimeout(() => {
        navigate("/");
      }, 1000);

    } catch (error) {
      console.error(error);

      toast.error(
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

        {/* Name */}
        <input
          type="text"
          name="name"
          placeholder="Full Name"
          value={formData.name}
          onChange={handleChange}
          className="w-full p-4 mb-4 border border-[#713600]/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#C05800]"
          required
        />

        {/* Email */}
        <input
          type="email"
          name="email"
          placeholder="Email Address"
          value={formData.email}
          onChange={handleChange}
          className="w-full p-4 mb-4 border border-[#713600]/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#C05800]"
          required
        />

        {/* Password */}
        <input
          type="password"
          name="password"
          placeholder="Password"
          value={formData.password}
          onChange={handleChange}
          className="w-full p-4 mb-4 border border-[#713600]/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#C05800]"
          required
        />
        <input
          type="text"
          name="team_id"
          placeholder="Team ID (Example: TEAM-001)"
          value={formData.team_id}
          onChange={handleChange}
          className="w-full p-4 mb-6 border border-[#713600]/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#C05800]"
          required
        />
        {/* Role */}
        <label className="block mb-2 text-[#713600] font-medium">
          Role
        </label>

        <select
          name="role"
          value={formData.role}
          onChange={handleChange}
          className="w-full p-4 mb-4 border border-[#713600]/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#C05800]"
        >
          <option value="employee">
            Employee
          </option>

          <option value="manager">
            Manager
          </option>
        </select>

        {/* Signup Button */}
        <button
          type="submit"
          disabled={isLoading}
          className={`w-full p-4 rounded-xl font-semibold text-white transition-all duration-300 ${
            isLoading
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-[#C05800] hover:bg-[#713600]"
          }`}
        >
          {isLoading
            ? "Creating Account..."
            : "Create Account"}
        </button>

      </form>

    </div>
  );
}

export default Signup;
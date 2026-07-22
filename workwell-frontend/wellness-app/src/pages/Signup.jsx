import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import API from "../services/api";

function Signup() {
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    company: "",
    team_id: "",
    role: "employee",
  });

  const [teams, setTeams] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [teamsLoading, setTeamsLoading] = useState(true);

  useEffect(() => {
    fetchTeams();
  }, []);

  const fetchTeams = async () => {
    try {
      setTeamsLoading(true);
      const response = await API.get("/teams");
      setTeams(response.data);
    } catch (error) {
      console.error("Failed to load teams:", error);
      toast.error("Unable to load teams. Please try again.");
    } finally {
      setTeamsLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }));
  };

  const handleSignup = async (e) => {
    e.preventDefault();

    if (isLoading) return;

    if (!formData.team_id) {
      toast.error("Please select a team.");
      return;
    }

    try {
      setIsLoading(true);

      await API.post("/auth/signup", formData);

      toast.success("Account created successfully!");

      setTimeout(() => {
        navigate("/");
      }, 1000);
    } catch (error) {
      console.error(error);
      toast.error(error.response?.data?.detail || "Signup failed");
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
          placeholder="Password (min 8 characters)"
          value={formData.password}
          onChange={handleChange}
          className="w-full p-4 mb-4 border border-[#713600]/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#C05800]"
          required
          minLength={8}
        />

        {/* Company */}
        <label className="block mb-2 text-[#713600] font-medium">
          Company
        </label>
        <input
          type="text"
          name="company"
          placeholder="Enter your company name"
          value={formData.company}
          onChange={handleChange}
          className="w-full p-4 mb-4 border border-[#713600]/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#C05800]"
          required
        />

        {/* Team */}
        <label className="block mb-2 text-[#713600] font-medium">
          Team
        </label>
        <select
          name="team_id"
          value={formData.team_id}
          onChange={handleChange}
          disabled={teamsLoading}
          className="w-full p-4 mb-4 border border-[#713600]/20 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-[#C05800] disabled:bg-gray-100"
          required
        >
          <option value="">
            {teamsLoading ? "Loading teams..." : "Select your team"}
          </option>
          {teams.map((team) => (
            <option key={team.id} value={team.id}>
              {team.name}
            </option>
          ))}
        </select>

        {/* Role */}
        <label className="block mb-2 text-[#713600] font-medium">
          Role
        </label>
        <select
          name="role"
          value={formData.role}
          onChange={handleChange}
          className="w-full p-4 mb-6 border border-[#713600]/20 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-[#C05800]"
          required
        >
          <option value="employee">Employee</option>
          <option value="manager">Manager</option>
        </select>

        {/* Signup Button */}
        <button
          type="submit"
          disabled={isLoading || teamsLoading || teams.length === 0}
          className={`w-full p-4 rounded-xl font-semibold text-white transition-all duration-300 ${
            isLoading || teamsLoading || teams.length === 0
              ? "bg-gray-400 cursor-not-allowed"
              : "bg-[#C05800] hover:bg-[#713600]"
          }`}
        >
          {isLoading
            ? "Creating Account..."
            : teamsLoading
            ? "Loading Teams..."
            : "Create Account"}
        </button>
      </form>
    </div>
  );
}

export default Signup;

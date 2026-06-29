import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import API from "../services/api";
import { toast } from "react-toastify";

function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();

    if (loading) return;

    setLoading(true);

    try {
      const response = await API.post("/auth/login", {
        email,
        password,
      });

      localStorage.setItem(
        "token",
        response.data.access_token
      );

      localStorage.setItem(
        "role",
        response.data.role
      );

      localStorage.setItem(
        "user_id",
        response.data.user_id
      );

      localStorage.setItem(
        "name",
        response.data.name
      );

      toast.success("Login Successful");

      if (response.data.role === "manager") {
        navigate("/manager");
      } else {
        navigate("/dashboard");
      }
    } catch (error) {
      console.log(error);

      toast.error("Invalid Email or Password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#FDFBD4] p-6">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-2xl p-8">

        {/* Heading */}
        <div className="mb-8 text-center">
          <h1 className="text-5xl font-bold text-[#38240D] mb-3">
            WorkWell
          </h1>

          <p className="text-[#713600]">
            AI Employee Wellness Platform
          </p>
        </div>

        {/* Login Form */}
        <form
          onSubmit={handleLogin}
          className="space-y-5"
        >

          {/* Email */}
          <div>
            <label className="block mb-2 text-[#713600] font-medium">
              Email
            </label>

            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) =>
                setEmail(e.target.value)
              }
              className="w-full p-4 rounded-2xl border border-[#713600]/20 focus:outline-none focus:ring-2 focus:ring-[#C05800]"
              required
            />
          </div>

          {/* Password */}
          <div>
            <label className="block mb-2 text-[#713600] font-medium">
              Password
            </label>

            <input
              type="password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) =>
                setPassword(e.target.value)
              }
              className="w-full p-4 rounded-2xl border border-[#713600]/20 focus:outline-none focus:ring-2 focus:ring-[#C05800]"
              required
            />
          </div>

          {/* Login Button */}
          <button
            type="submit"
            disabled={loading}
            className={`w-full py-4 rounded-2xl font-semibold text-white transition-all duration-300 ${
              loading
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-[#C05800] hover:bg-[#713600]"
            }`}
          >
            {loading
              ? "Logging in..."
              : "Login"}
          </button>

        </form>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-[#713600]">
            Don’t have an account?
          </p>

          <Link
            to="/signup"
            className="text-[#C05800] font-semibold hover:underline"
          >
            Create Account
          </Link>
        </div>

      </div>
    </div>
  );
}

export default Login;
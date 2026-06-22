import { BrowserRouter, Routes, Route } from "react-router-dom";

import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import WellnessForm from "./pages/WellnessForm";
import History from "./pages/History";
import ManagerDashboard from "./pages/ManagerDashboard";
import ProtectedRoute from "./components/ProtectedRoute";
import VoiceAssistant from "./pages/VoiceAssistant";
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
<Route
  path="/wellness"
  element={
    <ProtectedRoute
      allowedRole="employee"
    >
      <WellnessForm />
    </ProtectedRoute>
  }
/>
<Route
  path="/voice"
  element={<VoiceAssistant />}
/>        
<Route
  path="/history"
  element={
    <ProtectedRoute
      allowedRole="employee"
    >
      <History />
    </ProtectedRoute>
  }
/>
        <Route path="/dashboard" element={
          <ProtectedRoute
            allowedRole="employee"
          >
          <Dashboard />
          </ProtectedRoute>
        }
        />
        <Route path="/manager" element={
          <ProtectedRoute
            allowedRole="manager"
          >
          <ManagerDashboard />
          </ProtectedRoute>
        }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
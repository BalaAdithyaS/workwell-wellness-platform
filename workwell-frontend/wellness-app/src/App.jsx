import { BrowserRouter, Routes, Route } from "react-router-dom";

import Signup from "./pages/Signup";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import WellnessForm from "./pages/WellnessForm";
import History from "./pages/History";
import ManagerDashboard from "./pages/ManagerDashboard";
import VoiceAssistant from "./pages/VoiceAssistant";

import ProtectedRoute from "./components/ProtectedRoute";
import EmployeeLayout from "./components/EmployeeLayout";


function App() {
  return (
    <BrowserRouter>

      <Routes>

        {/* Public Routes */}
        <Route
          path="/"
          element={<Login />}
        />

        <Route
          path="/signup"
          element={<Signup />}
        />


        {/* Employee Routes with Shared Sidebar */}
        <Route
          element={
            <ProtectedRoute allowedRole="employee">
              <EmployeeLayout />
            </ProtectedRoute>
          }
        >

          <Route
            path="/dashboard"
            element={<Dashboard />}
          />

          <Route
            path="/wellness"
            element={<WellnessForm />}
          />

          <Route
            path="/history"
            element={<History />}
          />

          <Route
            path="/voice"
            element={<VoiceAssistant />}
          />

        </Route>


        {/* Manager Route */}
        <Route
          path="/manager"
          element={
            <ProtectedRoute allowedRole="manager">
              <ManagerDashboard />
            </ProtectedRoute>
          }
        />

      </Routes>

    </BrowserRouter>
  );
}

export default App;
import { Navigate } from "react-router-dom";

function ProtectedRoute({
  children,
  allowedRole,
}) {

  const token = localStorage.getItem(
    "token"
  );

  const role = localStorage.getItem(
    "role"
  );

  if (!token) {
    return <Navigate to="/" />;
  }

  if (
    allowedRole &&
    role !== allowedRole
  ) {
    return <Navigate to="/" />;
  }

  return children;
}

export default ProtectedRoute;
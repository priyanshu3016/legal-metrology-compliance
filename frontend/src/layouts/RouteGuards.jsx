import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export function RequireAuth({ children }) {
  const { isAuthenticated, isLoggingOut } = useAuth();
  const location = useLocation();
  if (!isAuthenticated) {
    if (isLoggingOut) {
      return <Navigate to="/" replace />;
    }
    return <Navigate to="/login" state={{ from: location }} replace />;
  }
  return children;
}

export function RedirectIfAuth({ children }) {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}

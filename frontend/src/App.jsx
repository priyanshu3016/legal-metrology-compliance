import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { InspectionProvider } from './context/InspectionContext';
import { ToastProvider } from './context/ToastContext';
import { RequireAuth, RedirectIfAuth } from './layouts/RouteGuards';
import { AppLayout } from './layouts/AppLayout';

// Pages (all default exports from subagent-generated files)
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import NewInspectionPage from './pages/NewInspectionPage';
import ProcessingPage from './pages/ProcessingPage';
import ResultPage from './pages/ResultPage';
import ViolationsPage from './pages/ViolationsPage';
import EvidencePage from './pages/EvidencePage';
import ReportPage from './pages/ReportPage';
import HistoryPage from './pages/HistoryPage';
import InspectionDetailPage from './pages/InspectionDetailPage';
import RulesPage from './pages/RulesPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <InspectionProvider>
          <ToastProvider>
            <Routes>
              {/* Public Root Landing Page */}
              <Route path="/" element={<LandingPage />} />

              {/* Public Officer Login */}
              <Route path="/login" element={<RedirectIfAuth><LoginPage /></RedirectIfAuth>} />

              {/* Protected - with AppLayout shell */}
              <Route element={<RequireAuth><AppLayout /></RequireAuth>}>
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/inspection/new" element={<NewInspectionPage />} />
                <Route path="/inspection/processing" element={<ProcessingPage />} />
                <Route path="/inspection/result" element={<ResultPage />} />
                <Route path="/inspection/violations" element={<ViolationsPage />} />
                <Route path="/inspection/evidence" element={<EvidencePage />} />
                <Route path="/inspection/report" element={<ReportPage />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/history/:id" element={<InspectionDetailPage />} />
                <Route path="/rules" element={<RulesPage />} />
                <Route path="/settings" element={<SettingsPage />} />
              </Route>

              {/* Fallback redirect */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ToastProvider>
        </InspectionProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

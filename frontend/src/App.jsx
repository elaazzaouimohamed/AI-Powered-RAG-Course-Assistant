import { Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext.jsx';
import Header from './components/layout/Header.jsx';
import Sidebar from './components/layout/Sidebar.jsx';
import ChatPage from './pages/ChatPage.jsx';
import LoginPage from './pages/LoginPage.jsx';
import AdminPage from './pages/AdminPage.jsx';
import HistoryPage from './pages/HistoryPage.jsx';
import { useAuth } from './hooks/useAuth.js';
import './App.css';

/**
 * Composant racine : fournit le contexte d'auth et orchestre le routage.
 *
 * Structure de la mise en page :
 *   <Sidebar /> (fixe à gauche)
 *   <main>
 *     <Header />
 *     <Routes> ... </Routes>
 *   </main>
 */
export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  );
}

/** Routes conditionnelles selon l'état d'authentification. */
function AppRoutes() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    );
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="app-content">
        <Header />
        <Routes>
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/history" element={<HistoryPage />} />
          {/* La page admin est accessible uniquement aux ADMIN — vérification dans le composant */}
          <Route path="/admin" element={<AdminPage />} />
          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Routes>
      </div>
    </div>
  );
}

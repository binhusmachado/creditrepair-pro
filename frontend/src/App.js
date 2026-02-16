import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ClientLogin from './pages/ClientPortal/ClientLogin';
import ClientDashboard from './pages/ClientPortal/ClientDashboard';
import PricingPage from './pages/ClientPortal/PricingPage';
import Dashboard from './pages/Dashboard';
import ClientList from './pages/ClientList';
import ClientDetail from './pages/ClientDetail';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async () => {
    try {
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data);
      }
    } catch (error) {
      console.error('Error fetching user:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Routes>
        <Route path="/login" element={
          user ? <Navigate to="/client/dashboard" /> : <ClientLogin setUser={setUser} />
        } />
        <Route path="/client/dashboard" element={
          user ? <ClientDashboard user={user} /> : <Navigate to="/login" />
        } />
        
        <Route path="/pricing" element={<PricingPage />} />
        
        <Route path="/admin/dashboard" element={
          user?.role === 'admin' ? <Dashboard /> : <Navigate to="/login" />
        } />
        
        <Route path="/admin/clients" element={
          user?.role === 'admin' ? <ClientList /> : <Navigate to="/login" />
        } />
        
        <Route path="/admin/clients/:id" element={
          user?.role === 'admin' ? <ClientDetail /> : <Navigate to="/login" />
        } />
        
        <Route path="/" element={<Navigate to={user ? "/client/dashboard" : "/login"} />} />
      </Routes>
    </div>
  );
}

export default App;
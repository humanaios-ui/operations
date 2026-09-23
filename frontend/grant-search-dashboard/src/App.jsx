import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import axios from 'axios';
import './styles/App.css';
import ProfileScreen from './pages/ProfileScreen';
import GrantSearchScreen from './pages/GrantSearchScreen';
import GrantDetailScreen from './pages/GrantDetailScreen';
import SavedGrantsScreen from './pages/SavedGrantsScreen';
import Navigation from './components/Navigation';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

function App() {
  const [nonprofitId, setNonprofitId] = useState(localStorage.getItem('nonprofitId') || null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (nonprofitId) {
      fetchProfile();
    }
  }, [nonprofitId]);

  const fetchProfile = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE}/nonprofits/${nonprofitId}`);
      setProfile(response.data);
      localStorage.setItem('nonprofitId', nonprofitId);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch profile');
      setProfile(null);
    } finally {
      setLoading(false);
    }
  };

  const handleProfileCreated = (newProfile) => {
    setProfile(newProfile);
    setNonprofitId(newProfile.nonprofit_id);
    localStorage.setItem('nonprofitId', newProfile.nonprofit_id);
  };

  const handleLogout = () => {
    setNonprofitId(null);
    setProfile(null);
    localStorage.removeItem('nonprofitId');
  };

  return (
    <Router>
      <div className="app">
        <Navigation
          profile={profile}
          onLogout={handleLogout}
          isAuthenticated={!!nonprofitId}
        />

        <div className="app-content">
          {error && <div className="error-banner">{error}</div>}

          <Routes>
            <Route
              path="/"
              element={
                !nonprofitId ? (
                  <ProfileScreen onProfileCreated={handleProfileCreated} isNew={true} />
                ) : (
                  <GrantSearchScreen
                    nonprofitId={nonprofitId}
                    profile={profile}
                    apiBase={API_BASE}
                  />
                )
              }
            />

            <Route
              path="/profile"
              element={
                nonprofitId ? (
                  <ProfileScreen
                    profileId={nonprofitId}
                    initialProfile={profile}
                    onProfileCreated={handleProfileCreated}
                    isNew={false}
                  />
                ) : (
                  <div>Please log in first</div>
                )
              }
            />

            <Route
              path="/search"
              element={
                nonprofitId ? (
                  <GrantSearchScreen
                    nonprofitId={nonprofitId}
                    profile={profile}
                    apiBase={API_BASE}
                  />
                ) : (
                  <div>Please log in first</div>
                )
              }
            />

            <Route
              path="/grant/:grantId"
              element={
                nonprofitId ? (
                  <GrantDetailScreen
                    nonprofitId={nonprofitId}
                    apiBase={API_BASE}
                  />
                ) : (
                  <div>Please log in first</div>
                )
              }
            />

            <Route
              path="/saved"
              element={
                nonprofitId ? (
                  <SavedGrantsScreen
                    nonprofitId={nonprofitId}
                    apiBase={API_BASE}
                  />
                ) : (
                  <div>Please log in first</div>
                )
              }
            />
          </Routes>
        </div>
      </div>
    </Router>
  );
}

export default App;

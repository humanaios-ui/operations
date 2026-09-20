import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import GrantCard from '../components/GrantCard';
import '../styles/SavedGrantsScreen.css';

function SavedGrantsScreen({ nonprofitId, apiBase }) {
  const [grants, setGrants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [savedGrantIds, setSavedGrantIds] = useState(new Set());
  const navigate = useNavigate();

  useEffect(() => {
    loadSavedGrants();
  }, []);

  const loadSavedGrants = async () => {
    setLoading(true);
    setError(null);

    try {
      // Get saved grant IDs from localStorage
      const saved = localStorage.getItem(`saved_grants_${nonprofitId}`);
      const grantIds = saved ? JSON.parse(saved) : [];
      setSavedGrantIds(new Set(grantIds));

      if (grantIds.length === 0) {
        setGrants([]);
        setLoading(false);
        return;
      }

      // Perform a search to get all grants and filter for saved ones
      // For now, we'll use a simple approach: search all grants and filter
      const response = await axios.post(
        `${apiBase}/nonprofits/${nonprofitId}/grants/search`,
        {
          focus_areas: null,
          service_geography: null,
          min_amount_usd: null,
          days_to_deadline_min: null,
          top_n: 100
        }
      );

      const allGrants = response.data.matches || [];
      const savedGrants = allGrants.filter(g => grantIds.includes(g.grant_id));
      setGrants(savedGrants);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load saved grants');
      setGrants([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSaveGrant = (grantId) => {
    const newSaved = new Set(savedGrantIds);
    if (newSaved.has(grantId)) {
      newSaved.delete(grantId);
      setGrants(grants.filter(g => g.grant_id !== grantId));
    } else {
      newSaved.add(grantId);
    }
    setSavedGrantIds(newSaved);
    localStorage.setItem(
      `saved_grants_${nonprofitId}`,
      JSON.stringify(Array.from(newSaved))
    );
  };

  const handleGrantClick = (grantId) => {
    const grant = grants.find(g => g.grant_id === grantId);
    navigate(`/grant/${grantId}`, { state: { grant } });
  };

  return (
    <div className="saved-grants-screen">
      <div className="saved-container">
        <div className="saved-header">
          <h1>Saved Grants</h1>
          <button className="back-button" onClick={() => navigate('/search')}>
            ← Back to Search
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        {loading && <p className="loading">Loading your saved grants...</p>}

        {!loading && grants.length === 0 && (
          <div className="no-saved-grants">
            <p>You haven't saved any grants yet.</p>
            <button onClick={() => navigate('/search')} className="search-button">
              Search for Grants
            </button>
          </div>
        )}

        {grants.length > 0 && (
          <>
            <div className="saved-summary">
              <h2>You have {grants.length} saved grant{grants.length !== 1 ? 's' : ''}</h2>
              <p className="summary-text">
                Review your saved grants and apply to the ones that match your capacity and mission.
              </p>
            </div>

            <div className="saved-grants-grid">
              {grants.map((grant) => (
                <GrantCard
                  key={grant.grant_id}
                  grant={grant}
                  isSaved={savedGrantIds.has(grant.grant_id)}
                  onSaveToggle={() => toggleSaveGrant(grant.grant_id)}
                  onClick={() => handleGrantClick(grant.grant_id)}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default SavedGrantsScreen;

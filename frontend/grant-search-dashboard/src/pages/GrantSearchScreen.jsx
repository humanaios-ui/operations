import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import GrantCard from '../components/GrantCard';
import FilterPanel from '../components/FilterPanel';
import '../styles/GrantSearchScreen.css';

function GrantSearchScreen({ nonprofitId, profile, apiBase }) {
  const [grants, setGrants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searched, setSearched] = useState(false);
  const [savedGrants, setSavedGrants] = useState(new Set());
  const navigate = useNavigate();

  const [filters, setFilters] = useState({
    focus_areas: [],
    service_geography: [],
    min_amount_usd: null,
    days_to_deadline_min: null,
    top_n: 15
  });

  useEffect(() => {
    loadSavedGrants();
  }, []);

  const loadSavedGrants = () => {
    const saved = localStorage.getItem(`saved_grants_${nonprofitId}`);
    if (saved) {
      try {
        setSavedGrants(new Set(JSON.parse(saved)));
      } catch (e) {
        console.error('Failed to load saved grants', e);
      }
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSearched(true);

    try {
      const response = await axios.post(
        `${apiBase}/nonprofits/${nonprofitId}/grants/search`,
        {
          focus_areas: filters.focus_areas.length > 0 ? filters.focus_areas : null,
          service_geography: filters.service_geography.length > 0 ? filters.service_geography : null,
          min_amount_usd: filters.min_amount_usd,
          days_to_deadline_min: filters.days_to_deadline_min,
          top_n: filters.top_n
        }
      );

      setGrants(response.data.matches || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search grants');
      setGrants([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleSaveGrant = (grantId) => {
    const newSaved = new Set(savedGrants);
    if (newSaved.has(grantId)) {
      newSaved.delete(grantId);
    } else {
      newSaved.add(grantId);
    }
    setSavedGrants(newSaved);
    localStorage.setItem(
      `saved_grants_${nonprofitId}`,
      JSON.stringify(Array.from(newSaved))
    );
  };

  const handleGrantClick = (grantId) => {
    navigate(`/grant/${grantId}`, { state: { grant: grants.find(g => g.grant_id === grantId) } });
  };

  return (
    <div className="grant-search-screen">
      <div className="search-container">
        <h1>Find Grants for {profile?.name}</h1>
        <p className="profile-summary">
          Organization: {profile?.name} | Annual Revenue: ${profile?.annual_revenue_usd?.toLocaleString() || 'N/A'}
          | Unrestricted Capital: ${profile?.unrestricted_capital_usd?.toLocaleString() || 'N/A'}
        </p>

        <form onSubmit={handleSearch} className="search-form">
          <FilterPanel
            filters={filters}
            onFiltersChange={setFilters}
            profile={profile}
          />
          <button type="submit" className="search-button" disabled={loading}>
            {loading ? 'Searching...' : 'Search Grants'}
          </button>
        </form>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="results-container">
        {searched && !loading && grants.length === 0 && (
          <p className="no-results">No grants found matching your criteria. Try adjusting your filters.</p>
        )}

        {grants.length > 0 && (
          <div className="results-summary">
            <h2>Results: {grants.length} matching grants</h2>
            <div className="grants-grid">
              {grants.map((grant) => (
                <GrantCard
                  key={grant.grant_id}
                  grant={grant}
                  isSaved={savedGrants.has(grant.grant_id)}
                  onSaveToggle={() => toggleSaveGrant(grant.grant_id)}
                  onClick={() => handleGrantClick(grant.grant_id)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default GrantSearchScreen;

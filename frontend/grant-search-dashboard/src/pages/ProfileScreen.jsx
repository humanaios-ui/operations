import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/ProfileScreen.css';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const VALID_FUNDING_SOURCES = [
  'government_grants', 'foundations', 'individual_donors',
  'corporate_sponsors', 'earned_income'
];

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
];

function ProfileScreen({ profileId, initialProfile, onProfileCreated, isNew }) {
  const [profile, setProfile] = useState(initialProfile || {
    nonprofit_id: '',
    name: '',
    ein: '',
    contact_email: '',
    website_url: '',
    contact_phone: '',
    annual_revenue_usd: '',
    unrestricted_capital_usd: '',
    mission_keywords: [],
    service_geography: [],
    nonprofit_legal_status: '501c3',
    fiscal_sponsor: '',
    years_operating: 1,
    irs_form_990_url: '',
    board_size: 0,
    executive_director_name: '',
    funding_sources: [],
    primary_funder: ''
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [keywordInput, setKeywordInput] = useState('');
  const [selectedStates, setSelectedStates] = useState(profile.service_geography || []);

  useEffect(() => {
    if (profile.service_geography) {
      setSelectedStates(profile.service_geography);
    }
  }, [profile.service_geography]);

  const handleInputChange = (e) => {
    const { name, value, type } = e.target;
    setProfile({
      ...profile,
      [name]: type === 'number' ? (value ? parseFloat(value) : '') : value
    });
  };

  const handleAddKeyword = () => {
    if (keywordInput.trim() && !profile.mission_keywords.includes(keywordInput.trim())) {
      setProfile({
        ...profile,
        mission_keywords: [...profile.mission_keywords, keywordInput.trim()]
      });
      setKeywordInput('');
    }
  };

  const handleRemoveKeyword = (keyword) => {
    setProfile({
      ...profile,
      mission_keywords: profile.mission_keywords.filter(k => k !== keyword)
    });
  };

  const toggleState = (state) => {
    const updated = selectedStates.includes(state)
      ? selectedStates.filter(s => s !== state)
      : [...selectedStates, state];
    setSelectedStates(updated);
    setProfile({ ...profile, service_geography: updated });
  };

  const toggleFundingSource = (source) => {
    const updated = profile.funding_sources.includes(source)
      ? profile.funding_sources.filter(f => f !== source)
      : [...profile.funding_sources, source];
    setProfile({ ...profile, funding_sources: updated });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      let response;
      if (isNew) {
        response = await axios.post(`${API_BASE}/nonprofits`, profile);
      } else {
        response = await axios.put(`${API_BASE}/nonprofits/${profileId}`, profile);
      }

      setProfile(response.data);
      setSuccess(true);
      onProfileCreated(response.data);

      setTimeout(() => setSuccess(false), 3000);
    } catch (err) {
      const errorMsg = err.response?.data?.errors
        ? Object.entries(err.response.data.errors).map(([key, val]) => `${key}: ${val}`).join(', ')
        : err.response?.data?.detail || 'Failed to save profile';
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-screen">
      <div className="profile-container">
        <h1>{isNew ? 'Create Your Nonprofit Profile' : 'Edit Profile'}</h1>
        {profile.profile_completion_pct !== undefined && (
          <div className="profile-completion">
            <span>Profile Completion: {(profile.profile_completion_pct * 100).toFixed(0)}%</span>
            <div className="completion-bar">
              <div
                className="completion-fill"
                style={{width: `${profile.profile_completion_pct * 100}%`}}
              ></div>
            </div>
          </div>
        )}

        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">Profile saved successfully!</div>}

        <form onSubmit={handleSubmit} className="profile-form">
          <fieldset>
            <legend>Organization Information</legend>

            <div className="form-group">
              <label>Organization Name *</label>
              <input
                type="text"
                name="name"
                value={profile.name}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label>EIN (XX-XXXXXXX) *</label>
              <input
                type="text"
                name="ein"
                value={profile.ein}
                onChange={handleInputChange}
                placeholder="12-3456789"
                required
              />
            </div>

            <div className="form-group">
              <label>Contact Email *</label>
              <input
                type="email"
                name="contact_email"
                value={profile.contact_email}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Website URL</label>
              <input
                type="url"
                name="website_url"
                value={profile.website_url}
                onChange={handleInputChange}
              />
            </div>

            <div className="form-group">
              <label>Contact Phone</label>
              <input
                type="tel"
                name="contact_phone"
                value={profile.contact_phone}
                onChange={handleInputChange}
              />
            </div>
          </fieldset>

          <fieldset>
            <legend>Financial Information</legend>

            <div className="form-group">
              <label>Annual Revenue (USD) *</label>
              <input
                type="number"
                name="annual_revenue_usd"
                value={profile.annual_revenue_usd}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="form-group">
              <label>Unrestricted Capital (USD)</label>
              <input
                type="number"
                name="unrestricted_capital_usd"
                value={profile.unrestricted_capital_usd}
                onChange={handleInputChange}
              />
            </div>
          </fieldset>

          <fieldset>
            <legend>Mission & Operations</legend>

            <div className="form-group">
              <label>Mission Keywords *</label>
              <div className="keyword-input">
                <input
                  type="text"
                  value={keywordInput}
                  onChange={(e) => setKeywordInput(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddKeyword())}
                  placeholder="e.g., education, STEM"
                />
                <button type="button" onClick={handleAddKeyword}>Add</button>
              </div>
              <div className="keywords-list">
                {profile.mission_keywords.map(kw => (
                  <span key={kw} className="keyword-tag">
                    {kw}
                    <button type="button" onClick={() => handleRemoveKeyword(kw)}>×</button>
                  </span>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Service Geography (States) *</label>
              <div className="states-grid">
                {US_STATES.map(state => (
                  <label key={state} className="state-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedStates.includes(state)}
                      onChange={() => toggleState(state)}
                    />
                    {state}
                  </label>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Years Operating</label>
              <input
                type="number"
                name="years_operating"
                value={profile.years_operating}
                onChange={handleInputChange}
                min="0"
              />
            </div>

            <div className="form-group">
              <label>Board Size</label>
              <input
                type="number"
                name="board_size"
                value={profile.board_size}
                onChange={handleInputChange}
                min="0"
              />
            </div>

            <div className="form-group">
              <label>Executive Director Name</label>
              <input
                type="text"
                name="executive_director_name"
                value={profile.executive_director_name}
                onChange={handleInputChange}
              />
            </div>
          </fieldset>

          <fieldset>
            <legend>Legal & Funding</legend>

            <div className="form-group">
              <label>Legal Status</label>
              <select
                name="nonprofit_legal_status"
                value={profile.nonprofit_legal_status}
                onChange={handleInputChange}
              >
                <option value="501c3">501(c)(3)</option>
                <option value="501c4">501(c)(4)</option>
                <option value="foreign">Foreign</option>
                <option value="other">Other</option>
              </select>
            </div>

            <div className="form-group">
              <label>Funding Sources *</label>
              <div className="checkbox-group">
                {VALID_FUNDING_SOURCES.map(source => (
                  <label key={source} className="checkbox">
                    <input
                      type="checkbox"
                      checked={profile.funding_sources.includes(source)}
                      onChange={() => toggleFundingSource(source)}
                    />
                    {source.replace(/_/g, ' ')}
                  </label>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>Primary Funder</label>
              <select
                name="primary_funder"
                value={profile.primary_funder}
                onChange={handleInputChange}
              >
                <option value="">Select...</option>
                <option value="government">Government</option>
                <option value="foundation">Foundation</option>
                <option value="corporate">Corporate</option>
                <option value="individual">Individual</option>
                <option value="earned_income">Earned Income</option>
              </select>
            </div>

            <div className="form-group">
              <label>IRS Form 990 URL</label>
              <input
                type="url"
                name="irs_form_990_url"
                value={profile.irs_form_990_url}
                onChange={handleInputChange}
              />
            </div>

            <div className="form-group">
              <label>Fiscal Sponsor</label>
              <input
                type="text"
                name="fiscal_sponsor"
                value={profile.fiscal_sponsor}
                onChange={handleInputChange}
              />
            </div>
          </fieldset>

          <div className="form-actions">
            <button type="submit" disabled={loading} className="submit-button">
              {loading ? 'Saving...' : isNew ? 'Create Profile' : 'Update Profile'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default ProfileScreen;

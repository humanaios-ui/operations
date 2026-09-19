import React from 'react';
import '../styles/FilterPanel.css';

const COMMON_FOCUS_AREAS = [
  'education', 'health', 'social_services', 'community_development',
  'environmental', 'arts_culture', 'research', 'economic_development'
];

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
];

function FilterPanel({ filters, onFiltersChange, profile }) {
  const handleFocusAreaChange = (area) => {
    const updated = filters.focus_areas.includes(area)
      ? filters.focus_areas.filter(a => a !== area)
      : [...filters.focus_areas, area];
    onFiltersChange({ ...filters, focus_areas: updated });
  };

  const handleStateChange = (state) => {
    const updated = filters.service_geography.includes(state)
      ? filters.service_geography.filter(s => s !== state)
      : [...filters.service_geography, state];
    onFiltersChange({ ...filters, service_geography: updated });
  };

  const handleMinAmountChange = (e) => {
    const value = e.target.value ? parseInt(e.target.value) : null;
    onFiltersChange({ ...filters, min_amount_usd: value });
  };

  const handleDeadlineChange = (e) => {
    const value = e.target.value ? parseInt(e.target.value) : null;
    onFiltersChange({ ...filters, days_to_deadline_min: value });
  };

  const handleTopNChange = (e) => {
    const value = e.target.value ? parseInt(e.target.value) : 15;
    onFiltersChange({ ...filters, top_n: value });
  };

  return (
    <div className="filter-panel">
      <div className="filter-section">
        <h3>Focus Areas</h3>
        <div className="filter-options">
          {COMMON_FOCUS_AREAS.map(area => (
            <label key={area} className="filter-checkbox">
              <input
                type="checkbox"
                checked={filters.focus_areas.includes(area)}
                onChange={() => handleFocusAreaChange(area)}
              />
              <span>{area.replace(/_/g, ' ')}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="filter-section">
        <h3>Service Geography</h3>
        <div className="filter-options states-grid">
          {US_STATES.map(state => (
            <label key={state} className="filter-checkbox state-checkbox">
              <input
                type="checkbox"
                checked={filters.service_geography.includes(state)}
                onChange={() => handleStateChange(state)}
              />
              <span>{state}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="filter-section">
        <h3>Minimum Grant Amount</h3>
        <input
          type="number"
          value={filters.min_amount_usd || ''}
          onChange={handleMinAmountChange}
          placeholder="e.g., 25000"
          className="filter-input"
        />
      </div>

      <div className="filter-section">
        <h3>Minimum Days to Deadline</h3>
        <input
          type="number"
          value={filters.days_to_deadline_min || ''}
          onChange={handleDeadlineChange}
          placeholder="e.g., 30"
          className="filter-input"
        />
      </div>

      <div className="filter-section">
        <h3>Number of Results</h3>
        <select value={filters.top_n} onChange={handleTopNChange} className="filter-select">
          <option value="5">Top 5</option>
          <option value="10">Top 10</option>
          <option value="15">Top 15 (default)</option>
          <option value="25">Top 25</option>
          <option value="50">Top 50</option>
        </select>
      </div>

      <div className="filter-summary">
        <p className="filters-applied">
          {filters.focus_areas.length > 0 && `Focus areas: ${filters.focus_areas.join(', ')}`}
          {filters.service_geography.length > 0 && ` | States: ${filters.service_geography.join(', ')}`}
          {filters.min_amount_usd && ` | Min amount: $${filters.min_amount_usd.toLocaleString()}`}
          {filters.days_to_deadline_min && ` | Min deadline: ${filters.days_to_deadline_min} days`}
        </p>
      </div>
    </div>
  );
}

export default FilterPanel;

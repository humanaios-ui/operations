import React from 'react';
import '../styles/GrantCard.css';

function GrantCard({ grant, isSaved, onSaveToggle, onClick }) {
  const getCapacityBadge = (verdict) => {
    if (verdict === 'GREEN_LIGHT') {
      return <span className="capacity-badge green">✓ Affordable</span>;
    }
    if (verdict === 'RED_LIGHT') {
      return (
        <span className="capacity-badge red">
          ✗ Shortfall: ${grant.capacity_shortfall_usd?.toLocaleString() || 'N/A'}
        </span>
      );
    }
    return <span className="capacity-badge neutral">Unknown</span>;
  };

  return (
    <div className="grant-card">
      <div className="grant-header">
        <div className="grant-title">
          <h3>{grant.funder}</h3>
          <span className="grant-amount">${grant.amount_usd?.toLocaleString() || 'N/A'}</span>
        </div>
        <button
          className={`save-button ${isSaved ? 'saved' : ''}`}
          onClick={(e) => {
            e.stopPropagation();
            onSaveToggle();
          }}
          title={isSaved ? 'Unsave grant' : 'Save grant'}
        >
          {isSaved ? '★' : '☆'}
        </button>
      </div>

      <div className="grant-content" onClick={onClick}>
        <div className="grant-score">
          <span className="score-label">Match Score:</span>
          <span className="score-value">{(grant.combined_score * 100).toFixed(0)}%</span>
        </div>

        <div className="grant-deadline">
          <span className="deadline-label">Deadline:</span>
          <span className="deadline-value">
            {grant.deadline} ({grant.days_until_deadline} days)
          </span>
        </div>

        <div className="grant-match-required">
          <span className="label">Nonprofit Match Required:</span>
          <span className="value">${grant.match_required_usd?.toLocaleString() || 'N/A'}</span>
        </div>

        <div className="grant-scores">
          <div className="score-item">
            <span className="label">Keywords:</span>
            <span className="bar">
              <span className="bar-fill" style={{width: `${grant.keyword_fit * 100}%`}}></span>
            </span>
            <span className="value">{(grant.keyword_fit * 100).toFixed(0)}%</span>
          </div>
          <div className="score-item">
            <span className="label">Geography:</span>
            <span className="bar">
              <span className="bar-fill" style={{width: `${grant.geography_fit * 100}%`}}></span>
            </span>
            <span className="value">{(grant.geography_fit * 100).toFixed(0)}%</span>
          </div>
          <div className="score-item">
            <span className="label">Budget:</span>
            <span className="bar">
              <span className="bar-fill" style={{width: `${grant.budget_fit * 100}%`}}></span>
            </span>
            <span className="value">{(grant.budget_fit * 100).toFixed(0)}%</span>
          </div>
          <div className="score-item">
            <span className="label">Timeline:</span>
            <span className="bar">
              <span className="bar-fill" style={{width: `${grant.timeline_fit * 100}%`}}></span>
            </span>
            <span className="value">{(grant.timeline_fit * 100).toFixed(0)}%</span>
          </div>
        </div>

        <div className="grant-capacity">
          <span className="label">Capacity Assessment:</span>
          {getCapacityBadge(grant.capacity_verdict)}
        </div>

        {grant.url && (
          <a href={grant.url} target="_blank" rel="noopener noreferrer" className="grant-link">
            View Grant Details →
          </a>
        )}
      </div>

      <div className="grant-footer">
        <button className="view-details-button" onClick={onClick}>
          View Details
        </button>
      </div>
    </div>
  );
}

export default GrantCard;

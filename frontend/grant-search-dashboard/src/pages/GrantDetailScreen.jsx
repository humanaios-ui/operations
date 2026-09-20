import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import '../styles/GrantDetailScreen.css';

function GrantDetailScreen({ nonprofitId, apiBase }) {
  const { grantId } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [grant, setGrant] = useState(location.state?.grant || null);
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem(`saved_grants_${nonprofitId}`);
    if (saved) {
      try {
        setIsSaved(JSON.parse(saved).includes(grantId));
      } catch (e) {
        console.error('Failed to check saved grants', e);
      }
    }
  }, [grantId, nonprofitId]);

  if (!grant) {
    return (
      <div className="grant-detail-screen">
        <div className="detail-container">
          <p>Grant details not found. Please search for grants first.</p>
          <button onClick={() => navigate('/search')}>Back to Search</button>
        </div>
      </div>
    );
  }

  const toggleSave = () => {
    const saved = localStorage.getItem(`saved_grants_${nonprofitId}`);
    let savedList = saved ? JSON.parse(saved) : [];

    if (isSaved) {
      savedList = savedList.filter(id => id !== grantId);
    } else {
      savedList.push(grantId);
    }

    localStorage.setItem(`saved_grants_${nonprofitId}`, JSON.stringify(savedList));
    setIsSaved(!isSaved);
  };

  return (
    <div className="grant-detail-screen">
      <div className="detail-container">
        <button className="back-button" onClick={() => navigate('/search')}>← Back to Search</button>

        <div className="detail-header">
          <div>
            <h1>{grant.funder}</h1>
            <span className="grant-id">Grant ID: {grant.grant_id}</span>
          </div>
          <button
            className={`save-button large ${isSaved ? 'saved' : ''}`}
            onClick={toggleSave}
          >
            {isSaved ? '★ Saved' : '☆ Save'}
          </button>
        </div>

        <div className="detail-content">
          <section className="detail-section">
            <h2>Grant Amount & Requirements</h2>
            <div className="detail-grid">
              <div className="detail-item">
                <span className="label">Grant Amount:</span>
                <span className="value">${grant.amount_usd?.toLocaleString() || 'N/A'}</span>
              </div>
              <div className="detail-item">
                <span className="label">Nonprofit Match Required:</span>
                <span className="value">${grant.match_required_usd?.toLocaleString() || 'N/A'}</span>
              </div>
              <div className="detail-item">
                <span className="label">Deadline:</span>
                <span className="value">{grant.deadline}</span>
              </div>
              <div className="detail-item">
                <span className="label">Days Until Deadline:</span>
                <span className="value">{grant.days_until_deadline}</span>
              </div>
            </div>
          </section>

          <section className="detail-section">
            <h2>Match Quality Analysis</h2>
            <div className="scores-detail">
              <div className="score-detail-item">
                <div className="score-header">
                  <span className="label">Keyword Fit:</span>
                  <span className="percentage">{(grant.keyword_fit * 100).toFixed(0)}%</span>
                </div>
                <div className="score-bar">
                  <span className="bar-fill" style={{width: `${grant.keyword_fit * 100}%`}}></span>
                </div>
                <p className="score-description">How well grant focus areas match your mission keywords</p>
              </div>

              <div className="score-detail-item">
                <div className="score-header">
                  <span className="label">Geographic Fit:</span>
                  <span className="percentage">{(grant.geography_fit * 100).toFixed(0)}%</span>
                </div>
                <div className="score-bar">
                  <span className="bar-fill" style={{width: `${grant.geography_fit * 100}%`}}></span>
                </div>
                <p className="score-description">Overlap between eligible states and your service areas</p>
              </div>

              <div className="score-detail-item">
                <div className="score-header">
                  <span className="label">Budget Fit:</span>
                  <span className="percentage">{(grant.budget_fit * 100).toFixed(0)}%</span>
                </div>
                <div className="score-bar">
                  <span className="bar-fill" style={{width: `${grant.budget_fit * 100}%`}}></span>
                </div>
                <p className="score-description">How well grant size matches your organization budget</p>
              </div>

              <div className="score-detail-item">
                <div className="score-header">
                  <span className="label">Timeline Fit:</span>
                  <span className="percentage">{(grant.timeline_fit * 100).toFixed(0)}%</span>
                </div>
                <div className="score-bar">
                  <span className="bar-fill" style={{width: `${grant.timeline_fit * 100}%`}}></span>
                </div>
                <p className="score-description">Time available before deadline</p>
              </div>

              <div className="overall-score">
                <span className="label">Overall Match Score:</span>
                <span className="value">{(grant.combined_score * 100).toFixed(0)}%</span>
              </div>
            </div>
          </section>

          <section className="detail-section">
            <h2>Capacity Assessment</h2>
            <div className={`capacity-assessment ${grant.capacity_verdict === 'GREEN_LIGHT' ? 'affordable' : 'not-affordable'}`}>
              {grant.capacity_verdict === 'GREEN_LIGHT' ? (
                <>
                  <h3>✓ Your organization can afford this match</h3>
                  <p>You have sufficient unrestricted capital to cover the required nonprofit match.</p>
                </>
              ) : (
                <>
                  <h3>✗ Capacity Shortfall</h3>
                  <p>
                    You would need an additional ${grant.capacity_shortfall_usd?.toLocaleString() || 'N/A'}
                    in unrestricted capital to meet the match requirement.
                  </p>
                  <p className="recommendation">
                    Consider: (1) fundraising first to build capital, (2) applying for a smaller grant,
                    or (3) seeking a co-applicant or fiscal sponsor to share the match requirement.
                  </p>
                </>
              )}
            </div>
          </section>

          {grant.focus_areas && grant.focus_areas.length > 0 && (
            <section className="detail-section">
              <h2>Focus Areas</h2>
              <div className="tags-list">
                {grant.focus_areas.map(area => (
                  <span key={area} className="tag">{area}</span>
                ))}
              </div>
            </section>
          )}

          {grant.eligible_states && grant.eligible_states.length > 0 && (
            <section className="detail-section">
              <h2>Eligible States</h2>
              <div className="states-list">
                {grant.eligible_states.map(state => (
                  <span key={state} className="state-tag">{state}</span>
                ))}
              </div>
            </section>
          )}

          <section className="detail-section">
            <h2>Next Steps</h2>
            <ol className="steps-list">
              <li>Review this grant information carefully</li>
              <li>Confirm your organization meets all eligibility requirements</li>
              <li>Prepare your proposal and supporting documents</li>
              {grant.capacity_verdict === 'RED_LIGHT' && (
                <li>Address the capacity shortfall before applying</li>
              )}
              <li>Submit your application before the deadline</li>
            </ol>
          </section>
        </div>

        <div className="detail-actions">
          {grant.url && (
            <a href={grant.url} target="_blank" rel="noopener noreferrer" className="apply-button">
              View Full Grant Details
            </a>
          )}
          <button className="back-button" onClick={() => navigate('/search')}>
            Back to Search Results
          </button>
        </div>
      </div>
    </div>
  );
}

export default GrantDetailScreen;

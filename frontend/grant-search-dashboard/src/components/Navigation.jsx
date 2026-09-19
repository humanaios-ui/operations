import React from 'react';
import { Link } from 'react-router-dom';
import '../styles/Navigation.css';

function Navigation({ profile, onLogout, isAuthenticated }) {
  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-logo">
          🎯 Grant Discovery Platform
        </Link>

        {isAuthenticated && (
          <ul className="navbar-menu">
            <li className="navbar-item">
              <Link to="/search" className="navbar-link">Search Grants</Link>
            </li>
            <li className="navbar-item">
              <Link to="/saved" className="navbar-link">Saved Grants</Link>
            </li>
            <li className="navbar-item">
              <Link to="/profile" className="navbar-link">My Profile</Link>
            </li>
            <li className="navbar-item">
              <span className="navbar-profile">
                {profile?.name || 'Nonprofit'}
              </span>
            </li>
            <li className="navbar-item">
              <button onClick={onLogout} className="navbar-logout">
                Logout
              </button>
            </li>
          </ul>
        )}
      </div>
    </nav>
  );
}

export default Navigation;

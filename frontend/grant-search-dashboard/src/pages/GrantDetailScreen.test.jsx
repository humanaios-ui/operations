import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter, Route, Routes } from 'react-router-dom';
import GrantDetailScreen from './GrantDetailScreen';
import axios from 'axios';

jest.mock('axios');

describe('GrantDetailScreen Component', () => {
  const mockGrant = {
    grant_id: 'g-001',
    funder: 'Tech Foundation',
    amount_usd: 50000,
    combined_score: 0.85,
    deadline: '2026-12-31',
    days_until_deadline: 407,
    match_required_usd: 10000,
    capacity_verdict: 'GREEN_LIGHT',
    capacity_shortfall_usd: 0,
    keyword_fit: 0.9,
    geography_fit: 0.8,
    budget_fit: 0.75,
    timeline_fit: 0.85,
    focus_areas: ['education', 'technology'],
    eligible_states: ['CA', 'NY', 'TX'],
    url: 'https://example.com/grant'
  };

  const renderWithGrantState = (grant) => {
    return render(
      <MemoryRouter initialEntries={[{ pathname: '/grant/g-001', state: { grant } }]}>
        <Routes>
          <Route
            path="/grant/:grantId"
            element={
              <GrantDetailScreen
                nonprofitId="np-001"
                apiBase="http://localhost:8000/api/v1"
              />
            }
          />
        </Routes>
      </MemoryRouter>
    );
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('renders grant detail information', () => {
    renderWithGrantState(mockGrant);
    expect(screen.getByText('Tech Foundation')).toBeInTheDocument();
  });

  test('displays capacity assessment as GREEN_LIGHT (Affordable)', () => {
    renderWithGrantState(mockGrant);
    expect(screen.getByText(/Your organization can afford this match/i)).toBeInTheDocument();
  });

  test('displays match score breakdown with progress bars', () => {
    renderWithGrantState(mockGrant);
    expect(screen.getByText(/Keyword Fit:/i)).toBeInTheDocument();
    expect(screen.getByText(/Geographic Fit:/i)).toBeInTheDocument();
  });

  test('saves grant to localStorage when save button clicked', () => {
    renderWithGrantState(mockGrant);
    const saveButton = screen.getByRole('button', { name: /☆ Save/i });
    fireEvent.click(saveButton);

    const saved = JSON.parse(localStorage.getItem('saved_grants_np-001') || '[]');
    expect(saved).toContain('g-001');
  });

  test('displays focus areas tags if available', () => {
    renderWithGrantState(mockGrant);
    expect(screen.getByText('education')).toBeInTheDocument();
    expect(screen.getByText('technology')).toBeInTheDocument();
  });

  test('displays eligible states as tags', () => {
    renderWithGrantState(mockGrant);
    expect(screen.getByText('CA')).toBeInTheDocument();
    expect(screen.getByText('NY')).toBeInTheDocument();
  });

  test('displays RED_LIGHT verdict with shortfall amount', () => {
    const redLightGrant = {
      ...mockGrant,
      capacity_verdict: 'RED_LIGHT',
      capacity_shortfall_usd: 15000
    };

    renderWithGrantState(redLightGrant);
    expect(screen.getByText(/Capacity Shortfall/i)).toBeInTheDocument();
  });
});

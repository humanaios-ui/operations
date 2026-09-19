import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter, Route, Routes } from 'react-router-dom';
import GrantDetailScreen from './GrantDetailScreen';
import axios from 'axios';

jest.mock('axios');

describe('GrantDetailScreen Component', () => {
  const mockGrant = {
    grant_id: 'g-001',
    funder_name: 'Tech Foundation',
    amount_usd: 50000,
    match_score: 0.85,
    deadline: '2026-12-31',
    nonprofit_match_usd: 10000,
    capacity_verdict: 'GREEN_LIGHT',
    shortfall_amount: 0,
    component_scores: {
      keyword_fit: 0.9,
      geography_fit: 0.8,
      budget_fit: 0.75,
      timeline_fit: 0.85
    },
    focus_areas: ['education', 'technology'],
    eligible_states: ['CA', 'NY', 'TX'],
    url: 'https://example.com/grant'
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('renders grant detail information', () => {
    render(
      <MemoryRouter initialEntries={['/grant/g-001']}>
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
      </MemoryRouter>,
      { state: { grant: mockGrant } }
    );

    expect(screen.getByText('Tech Foundation')).toBeInTheDocument();
  });

  test('displays capacity assessment as GREEN_LIGHT (Affordable)', () => {
    render(
      <MemoryRouter initialEntries={['/grant/g-001']}>
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
      </MemoryRouter>,
      { state: { grant: mockGrant } }
    );

    expect(screen.getByText(/Affordable|GREEN_LIGHT/i)).toBeInTheDocument();
  });

  test('displays match score breakdown with progress bars', () => {
    render(
      <MemoryRouter initialEntries={['/grant/g-001']}>
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
      </MemoryRouter>,
      { state: { grant: mockGrant } }
    );

    expect(screen.getByText(/Keyword Fit|keyword/i)).toBeInTheDocument();
    expect(screen.getByText(/Geography Fit|geography/i)).toBeInTheDocument();
  });

  test('saves grant to localStorage when save button clicked', () => {
    render(
      <MemoryRouter initialEntries={['/grant/g-001']}>
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
      </MemoryRouter>,
      { state: { grant: mockGrant } }
    );

    const saveButtons = screen.getAllByRole('button', { name: /★/i });
    fireEvent.click(saveButtons[0]);

    const saved = JSON.parse(localStorage.getItem('saved_grants_np-001') || '[]');
    expect(saved).toContain('g-001');
  });

  test('displays focus areas tags if available', () => {
    render(
      <MemoryRouter initialEntries={['/grant/g-001']}>
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
      </MemoryRouter>,
      { state: { grant: mockGrant } }
    );

    expect(screen.getByText('education')).toBeInTheDocument();
    expect(screen.getByText('technology')).toBeInTheDocument();
  });

  test('displays eligible states as tags', () => {
    render(
      <MemoryRouter initialEntries={['/grant/g-001']}>
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
      </MemoryRouter>,
      { state: { grant: mockGrant } }
    );

    expect(screen.getByText('CA')).toBeInTheDocument();
    expect(screen.getByText('NY')).toBeInTheDocument();
  });

  test('displays RED_LIGHT verdict with shortfall amount', () => {
    const redLightGrant = {
      ...mockGrant,
      capacity_verdict: 'RED_LIGHT',
      shortfall_amount: 15000
    };

    render(
      <MemoryRouter initialEntries={['/grant/g-001']}>
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
      </MemoryRouter>,
      { state: { grant: redLightGrant } }
    );

    expect(screen.getByText(/Shortfall|RED_LIGHT|Capacity/i)).toBeInTheDocument();
  });
});

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import SavedGrantsScreen from './SavedGrantsScreen';
import axios from 'axios';

jest.mock('axios');

describe('SavedGrantsScreen Component', () => {
  const mockGrants = [
    {
      grant_id: 'g-001',
      funder: 'Foundation A',
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
      timeline_fit: 0.85
    },
    {
      grant_id: 'g-002',
      funder: 'Foundation B',
      amount_usd: 75000,
      combined_score: 0.92,
      deadline: '2026-11-30',
      days_until_deadline: 377,
      match_required_usd: 15000,
      capacity_verdict: 'GREEN_LIGHT',
      capacity_shortfall_usd: 0,
      keyword_fit: 0.95,
      geography_fit: 0.85,
      budget_fit: 0.9,
      timeline_fit: 0.92
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('renders saved grants screen with title', () => {
    localStorage.setItem('saved_grants_np-001', JSON.stringify([]));
    axios.post.mockResolvedValueOnce({ data: { matches: [] } });

    render(
      <BrowserRouter>
        <SavedGrantsScreen
          nonprofitId="np-001"
          apiBase="http://localhost:8000/api/v1"
        />
      </BrowserRouter>
    );

    expect(screen.getByText('Saved Grants')).toBeInTheDocument();
  });

  test('displays empty state message when no saved grants', async () => {
    localStorage.setItem('saved_grants_np-001', JSON.stringify([]));
    axios.post.mockResolvedValueOnce({ data: { matches: [] } });

    render(
      <BrowserRouter>
        <SavedGrantsScreen
          nonprofitId="np-001"
          apiBase="http://localhost:8000/api/v1"
        />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/haven't saved any grants/i)).toBeInTheDocument();
    });
  });

  test('loads and displays saved grants from localStorage', async () => {
    const savedIds = ['g-001', 'g-002'];
    localStorage.setItem('saved_grants_np-001', JSON.stringify(savedIds));
    axios.post.mockResolvedValueOnce({ data: { matches: mockGrants } });

    render(
      <BrowserRouter>
        <SavedGrantsScreen
          nonprofitId="np-001"
          apiBase="http://localhost:8000/api/v1"
        />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Foundation A')).toBeInTheDocument();
      expect(screen.getByText('Foundation B')).toBeInTheDocument();
    });
  });

  test('displays saved grants count', async () => {
    const savedIds = ['g-001', 'g-002'];
    localStorage.setItem('saved_grants_np-001', JSON.stringify(savedIds));
    axios.post.mockResolvedValueOnce({ data: { matches: mockGrants } });

    render(
      <BrowserRouter>
        <SavedGrantsScreen
          nonprofitId="np-001"
          apiBase="http://localhost:8000/api/v1"
        />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/You have 2 saved grants/i)).toBeInTheDocument();
    });
  });

  test('removes grant from saved when unsave is clicked', async () => {
    const savedIds = ['g-001', 'g-002'];
    localStorage.setItem('saved_grants_np-001', JSON.stringify(savedIds));
    axios.post.mockResolvedValueOnce({ data: { matches: mockGrants } });

    render(
      <BrowserRouter>
        <SavedGrantsScreen
          nonprofitId="np-001"
          apiBase="http://localhost:8000/api/v1"
        />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Foundation A')).toBeInTheDocument();
    });

    const saveButtons = screen.getAllByRole('button', { name: /★/i });
    fireEvent.click(saveButtons[0]);

    const updated = JSON.parse(localStorage.getItem('saved_grants_np-001'));
    expect(updated).toHaveLength(1);
    expect(updated).not.toContain('g-001');
  });

  test('calls API with correct parameters', async () => {
    const savedIds = ['g-001'];
    localStorage.setItem('saved_grants_np-001', JSON.stringify(savedIds));
    axios.post.mockResolvedValueOnce({ data: { matches: [mockGrants[0]] } });

    render(
      <BrowserRouter>
        <SavedGrantsScreen
          nonprofitId="np-001"
          apiBase="http://localhost:8000/api/v1"
        />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/nonprofits/np-001/grants/search',
        expect.objectContaining({
          top_n: 100
        })
      );
    });
  });

  test('displays search button to navigate to search grants', async () => {
    localStorage.setItem('saved_grants_np-001', JSON.stringify([]));
    axios.post.mockResolvedValueOnce({ data: { matches: [] } });

    render(
      <BrowserRouter>
        <SavedGrantsScreen
          nonprofitId="np-001"
          apiBase="http://localhost:8000/api/v1"
        />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Search for Grants/i })).toBeInTheDocument();
    });
  });
});

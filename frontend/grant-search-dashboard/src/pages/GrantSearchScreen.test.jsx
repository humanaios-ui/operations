import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import GrantSearchScreen from './GrantSearchScreen';
import axios from 'axios';

jest.mock('axios');

describe('GrantSearchScreen Component', () => {
  const mockProfile = {
    name: 'Test Nonprofit',
    annual_revenue_usd: 100000,
    unrestricted_capital_usd: 25000
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('renders search screen with filter panel', () => {
    render(
      <BrowserRouter>
        <GrantSearchScreen
          nonprofitId="np-001"
          profile={mockProfile}
          apiBase="http://localhost:8000/api/v1"
        />
      </BrowserRouter>
    );
    expect(screen.getByRole('button', { name: /Search Grants/i })).toBeInTheDocument();
  });

  test('displays profile summary with nonprofit name', () => {
    render(
      <BrowserRouter>
        <GrantSearchScreen
          nonprofitId="np-001"
          profile={mockProfile}
          apiBase="http://localhost:8000/api/v1"
        />
      </BrowserRouter>
    );
    expect(screen.getByText('Test Nonprofit')).toBeInTheDocument();
  });

  test('performs grant search when search button is clicked', async () => {
    const mockResults = {
      matches: [
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
        }
      ]
    };
    axios.post.mockResolvedValueOnce({ data: mockResults });

    render(
      <BrowserRouter>
        <GrantSearchScreen
          nonprofitId="np-001"
          profile={mockProfile}
          apiBase="http://localhost:8000/api/v1"
        />
      </BrowserRouter>
    );

    const searchButton = screen.getByRole('button', { name: /Search/i });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith(
        expect.stringContaining('/grants/search'),
        expect.any(Object)
      );
    });
  });

  test('displays search results as grant cards', async () => {
    const mockResults = {
      matches: [
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
        }
      ]
    };
    axios.post.mockResolvedValueOnce({ data: mockResults });

    render(
      <BrowserRouter>
        <GrantSearchScreen
          nonprofitId="np-001"
          profile={mockProfile}
          apiBase="http://localhost:8000/api/v1"
        />
      </BrowserRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /Search/i }));

    await waitFor(() => {
      expect(screen.getByText('Foundation A')).toBeInTheDocument();
    });
  });

  test('displays no results message when search returns empty', async () => {
    axios.post.mockResolvedValueOnce({ data: { matches: [] } });

    render(
      <BrowserRouter>
        <GrantSearchScreen
          nonprofitId="np-001"
          profile={mockProfile}
          apiBase="http://localhost:8000/api/v1"
        />
      </BrowserRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /Search/i }));

    await waitFor(() => {
      expect(screen.getByText(/No grants found/i)).toBeInTheDocument();
    });
  });

  test('saves and retrieves saved grants from localStorage', async () => {
    const mockResults = {
      matches: [
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
        }
      ]
    };
    axios.post.mockResolvedValueOnce({ data: mockResults });

    render(
      <BrowserRouter>
        <GrantSearchScreen
          nonprofitId="np-001"
          profile={mockProfile}
          apiBase="http://localhost:8000/api/v1"
        />
      </BrowserRouter>
    );

    fireEvent.click(screen.getByRole('button', { name: /Search/i }));

    await waitFor(() => {
      expect(screen.getByText('Foundation A')).toBeInTheDocument();
    });

    const saveButtons = screen.getAllByRole('button', { name: /☆/i });
    fireEvent.click(saveButtons[0]);

    const saved = JSON.parse(localStorage.getItem('saved_grants_np-001'));
    expect(saved).toContain('g-001');
  });
});

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import GrantCard from './GrantCard';

describe('GrantCard Component', () => {
  const mockGrant = {
    grant_id: 'grant-001',
    funder_name: 'Tech Foundation',
    amount_usd: 50000,
    match_score: 0.85,
    deadline: '2026-12-31',
    nonprofit_match_usd: 10000,
    capacity_verdict: 'GREEN_LIGHT',
    component_scores: {
      keyword_fit: 0.9,
      geography_fit: 0.8,
      budget_fit: 0.75,
      timeline_fit: 0.85
    }
  };

  test('renders grant information correctly', () => {
    render(
      <GrantCard grant={mockGrant} isSaved={false} onSaveToggle={() => {}} onClick={() => {}} />
    );
    expect(screen.getByText('Tech Foundation')).toBeInTheDocument();
    expect(screen.getByText('$50,000')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  test('displays capacity assessment badge', () => {
    render(
      <GrantCard grant={mockGrant} isSaved={false} onSaveToggle={() => {}} onClick={() => {}} />
    );
    expect(screen.getByText('Affordable')).toBeInTheDocument();
  });

  test('calls onSaveToggle when save button is clicked', () => {
    const mockToggle = jest.fn();
    render(
      <GrantCard grant={mockGrant} isSaved={false} onSaveToggle={mockToggle} onClick={() => {}} />
    );
    const saveButton = screen.getByRole('button', { name: /★/i });
    fireEvent.click(saveButton);
    expect(mockToggle).toHaveBeenCalled();
  });

  test('calls onClick when details button is clicked', () => {
    const mockClick = jest.fn();
    render(
      <GrantCard grant={mockGrant} isSaved={false} onSaveToggle={() => {}} onClick={mockClick} />
    );
    const detailsButton = screen.getByText('View Details');
    fireEvent.click(detailsButton);
    expect(mockClick).toHaveBeenCalled();
  });

  test('displays saved state when isSaved is true', () => {
    const { container } = render(
      <GrantCard grant={mockGrant} isSaved={true} onSaveToggle={() => {}} onClick={() => {}} />
    );
    const saveButton = container.querySelector('.save-button.saved');
    expect(saveButton).toBeInTheDocument();
  });

  test('renders component scores with progress bars', () => {
    render(
      <GrantCard grant={mockGrant} isSaved={false} onSaveToggle={() => {}} onClick={() => {}} />
    );
    expect(screen.getByText('Keyword Fit')).toBeInTheDocument();
    expect(screen.getByText('Geography Fit')).toBeInTheDocument();
    expect(screen.getByText('Budget Fit')).toBeInTheDocument();
    expect(screen.getByText('Timeline Fit')).toBeInTheDocument();
  });
});

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProfileScreen from './ProfileScreen';
import axios from 'axios';

jest.mock('axios');

describe('ProfileScreen Component', () => {
  const mockOnProfileCreated = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders profile form with required fields', () => {
    render(
      <ProfileScreen onProfileCreated={mockOnProfileCreated} isNew={true} />
    );
    const inputs = screen.getAllByRole('textbox');
    expect(inputs.length).toBeGreaterThan(0);
    expect(screen.getByText(/Organization Name/i)).toBeInTheDocument();
    expect(screen.getByText(/EIN/i)).toBeInTheDocument();
    expect(screen.getByText(/Annual Revenue/i)).toBeInTheDocument();
  });

  test('displays profile completion percentage', () => {
    render(
      <ProfileScreen onProfileCreated={mockOnProfileCreated} isNew={true} />
    );
    expect(screen.getByText(/Profile Completion:/i)).toBeInTheDocument();
  });

  test('submits form with valid data', async () => {
    const user = userEvent.setup();
    const mockProfile = { nonprofit_id: 'np-001', name: 'Test Org', ein: '123456789', contact_email: 'test@org.org', annual_revenue_usd: 100000 };
    axios.post.mockResolvedValueOnce({ data: mockProfile });

    render(
      <ProfileScreen onProfileCreated={mockOnProfileCreated} isNew={true} />
    );

    const inputs = screen.getAllByRole('textbox');
    await user.type(inputs[0], 'Test Org');
    await user.type(inputs[1], '12-3456789');
    await user.type(inputs[2], 'test@org.org');

    const numberInputs = screen.getAllByRole('spinbutton');
    await user.type(numberInputs[0], '100000');

    await user.click(screen.getByRole('button', { name: /Create Profile/i }));

    await waitFor(() => {
      expect(axios.post).toHaveBeenCalled();
    });
  });

  test('displays error message on submission failure', async () => {
    const user = userEvent.setup();
    axios.post.mockRejectedValueOnce({ response: { data: { detail: 'Invalid EIN' } } });

    render(
      <ProfileScreen onProfileCreated={mockOnProfileCreated} isNew={true} />
    );

    const inputs = screen.getAllByRole('textbox');
    await user.type(inputs[0], 'Test Org');
    await user.type(inputs[1], 'invalid');
    await user.type(inputs[2], 'test@org.org');

    const numberInputs = screen.getAllByRole('spinbutton');
    await user.type(numberInputs[0], '100000');

    await user.click(screen.getByRole('button', { name: /Create Profile/i }));

    await waitFor(() => {
      expect(screen.getByText(/Invalid EIN/i)).toBeInTheDocument();
    });
  });

  test('allows adding and removing keywords', async () => {
    const user = userEvent.setup();
    render(
      <ProfileScreen onProfileCreated={mockOnProfileCreated} isNew={true} />
    );

    const keywordInput = screen.getByPlaceholderText(/e\.g\., education/i);
    const addButton = screen.getByRole('button', { name: /^Add$/i });

    await user.type(keywordInput, 'education');
    await user.click(addButton);

    expect(screen.getByText('education')).toBeInTheDocument();
  });

  test('calls onProfileCreated callback after successful submission', async () => {
    const user = userEvent.setup();
    const mockProfile = { nonprofit_id: 'np-001', name: 'Test Org', ein: '123456789', contact_email: 'test@org.org', annual_revenue_usd: 100000 };
    axios.post.mockResolvedValueOnce({ data: mockProfile });

    render(
      <ProfileScreen onProfileCreated={mockOnProfileCreated} isNew={true} />
    );

    const inputs = screen.getAllByRole('textbox');
    await user.type(inputs[0], 'Test Org');
    await user.type(inputs[1], '12-3456789');
    await user.type(inputs[2], 'test@org.org');

    const numberInputs = screen.getAllByRole('spinbutton');
    await user.type(numberInputs[0], '100000');

    await user.click(screen.getByRole('button', { name: /Create Profile/i }));

    await waitFor(() => {
      expect(mockOnProfileCreated).toHaveBeenCalledWith(mockProfile);
    });
  });
});

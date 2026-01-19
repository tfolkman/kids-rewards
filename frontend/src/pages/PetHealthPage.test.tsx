import React from 'react';
import { render, screen, waitFor } from '../test-utils';
import PetHealthPage from './PetHealthPage';
import * as api from '../services/api';

jest.mock('../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('PetHealthPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders page title', async () => {
    mockedApi.getPets.mockResolvedValue({ data: [] } as any);

    render(<PetHealthPage />);

    await waitFor(() => {
      expect(screen.getByText('Pet Health Tracking')).toBeInTheDocument();
    });
  });

  test('calls getPets on mount', async () => {
    mockedApi.getPets.mockResolvedValue({ data: [] } as any);

    render(<PetHealthPage />);

    await waitFor(() => {
      expect(mockedApi.getPets).toHaveBeenCalled();
    });
  });

  test('shows message when no pets exist', async () => {
    mockedApi.getPets.mockResolvedValue({ data: [] } as any);

    render(<PetHealthPage />);

    await waitFor(() => {
      expect(screen.getByText('No pets found. Add a pet first to track health.')).toBeInTheDocument();
    });
  });
});

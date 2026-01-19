import React from 'react';
import { render, screen, waitFor } from '../test-utils';
import ManagePetsPage from './ManagePetsPage';
import * as api from '../services/api';

jest.mock('../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('ManagePetsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders page title', async () => {
    mockedApi.getPets.mockResolvedValue({ data: [] } as any);

    render(<ManagePetsPage />);

    await waitFor(() => {
      expect(screen.getByText('Manage Pets')).toBeInTheDocument();
    });
  });

  test('shows Add Pet button', async () => {
    mockedApi.getPets.mockResolvedValue({ data: [] } as any);

    render(<ManagePetsPage />);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add new pet/i })).toBeInTheDocument();
    });
  });

  test('shows empty state when no pets', async () => {
    mockedApi.getPets.mockResolvedValue({ data: [] } as any);

    render(<ManagePetsPage />);

    await waitFor(() => {
      expect(screen.getByText(/No pets added yet/i)).toBeInTheDocument();
    });
  });

  test('displays pets when data is returned', async () => {
    const mockPets = [
      {
        id: '1',
        name: 'Spike',
        species: 'bearded_dragon',
        birthday: '2025-02-01',
        is_active: true,
        parent_id: 'parent1',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        age_months: 11,
        life_stage: 'juvenile',
      },
    ];
    mockedApi.getPets.mockResolvedValue({ data: mockPets } as any);

    render(<ManagePetsPage />);

    await waitFor(() => {
      expect(screen.getByText('Spike')).toBeInTheDocument();
    });
  });

  test('calls getPets on mount', async () => {
    mockedApi.getPets.mockResolvedValue({ data: [] } as any);

    render(<ManagePetsPage />);

    await waitFor(() => {
      expect(mockedApi.getPets).toHaveBeenCalled();
    });
  });
});

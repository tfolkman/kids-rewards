import React from 'react';
import { render, screen, waitFor } from '../test-utils';
import MyPetTasksPage from './MyPetTasksPage';
import * as api from '../services/api';

jest.mock('../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('MyPetTasksPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders page title', async () => {
    mockedApi.getMyPetTasks.mockResolvedValue({ data: [] } as any);

    render(<MyPetTasksPage />);

    await waitFor(() => {
      expect(screen.getByText('My Pet Tasks')).toBeInTheDocument();
    });
  });

  test('shows empty state when no tasks', async () => {
    mockedApi.getMyPetTasks.mockResolvedValue({ data: [] } as any);

    render(<MyPetTasksPage />);

    await waitFor(() => {
      expect(screen.getByText('No pet care tasks assigned to you yet.')).toBeInTheDocument();
    });
  });

  test('displays assigned tasks in To Do section', async () => {
    const mockTasks = [
      {
        id: '1',
        schedule_id: 'sched1',
        pet_id: 'pet1',
        pet_name: 'Spike',
        task_name: 'Feed Spike',
        description: 'Give Spike his daily food',
        assigned_to_kid_id: 'kid1',
        assigned_to_kid_username: 'testkid',
        due_date: '2025-01-20',
        status: 'assigned',
        points_value: 10,
        created_at: '2025-01-01T00:00:00Z',
      },
    ];
    mockedApi.getMyPetTasks.mockResolvedValue({ data: mockTasks } as any);

    render(<MyPetTasksPage />);

    await waitFor(() => {
      expect(screen.getByText('To Do')).toBeInTheDocument();
      expect(screen.getByText('Feed Spike')).toBeInTheDocument();
    });
  });

  test('displays pending approval tasks', async () => {
    const mockTasks = [
      {
        id: '1',
        schedule_id: 'sched1',
        pet_id: 'pet1',
        pet_name: 'Spike',
        task_name: 'Feed Spike',
        assigned_to_kid_id: 'kid1',
        assigned_to_kid_username: 'testkid',
        due_date: '2025-01-20',
        status: 'pending_approval',
        points_value: 10,
        submitted_at: '2025-01-18T10:00:00Z',
        created_at: '2025-01-01T00:00:00Z',
      },
    ];
    mockedApi.getMyPetTasks.mockResolvedValue({ data: mockTasks } as any);

    render(<MyPetTasksPage />);

    await waitFor(() => {
      expect(screen.getByText('Awaiting Approval')).toBeInTheDocument();
    });
  });

  test('displays completed tasks in History section', async () => {
    const mockTasks = [
      {
        id: '1',
        schedule_id: 'sched1',
        pet_id: 'pet1',
        pet_name: 'Spike',
        task_name: 'Feed Spike',
        assigned_to_kid_id: 'kid1',
        assigned_to_kid_username: 'testkid',
        due_date: '2025-01-20',
        status: 'approved',
        points_value: 10,
        reviewed_at: '2025-01-18T12:00:00Z',
        created_at: '2025-01-01T00:00:00Z',
      },
    ];
    mockedApi.getMyPetTasks.mockResolvedValue({ data: mockTasks } as any);

    render(<MyPetTasksPage />);

    await waitFor(() => {
      expect(screen.getByText('History')).toBeInTheDocument();
    });
  });

  test('calls getMyPetTasks on mount', async () => {
    mockedApi.getMyPetTasks.mockResolvedValue({ data: [] } as any);

    render(<MyPetTasksPage />);

    await waitFor(() => {
      expect(mockedApi.getMyPetTasks).toHaveBeenCalled();
    });
  });
});

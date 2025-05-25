import React, { useState, useEffect } from 'react';
import * as api from '../services/api';
import { ChoreLogWithStreakBonus, ChoreStatus } from '../services/api';
import {
  Text,
  Paper,
  Loader,
  Alert,
  Title,
  Container,
  Stack,
  Badge,
  Group,
  Tooltip,
  Card,
} from '@mantine/core';
import { IconAlertCircle, IconFlame, IconCalendar, IconCoins } from '@tabler/icons-react';
import { ResponsiveTable } from '../components/ResponsiveTable';

const ChoreHistoryPage: React.FC = () => {
  const [choreHistory, setChoreHistory] = useState<ChoreLogWithStreakBonus[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchChoreHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // Try the detailed endpoint first
      const response = await api.getMyDetailedChoreHistory();
      // Data is already sorted by the backend (newest first)
      setChoreHistory(response.data);
    } catch (err: any) {
      // If detailed endpoint fails (404), fall back to regular endpoint
      if (err.response?.status === 404) {
        try {
          const fallbackResponse = await api.getMyChoreHistory();
          // Sort by submitted_at date, newest first
          const sortedHistory = fallbackResponse.data.sort((a, b) => 
            new Date(b.submitted_at).getTime() - new Date(a.submitted_at).getTime()
          );
          // Convert to ChoreLogWithStreakBonus format (without bonus data)
          setChoreHistory(sortedHistory.map(log => ({
            ...log,
            streak_bonus_points: undefined,
            streak_day: undefined
          })));
        } catch (fallbackErr) {
          setError('Failed to fetch chore history. Please try again.');
          console.error(fallbackErr);
        }
      } else {
        setError('Failed to fetch chore history. Please try again.');
        console.error(err);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchChoreHistory();
  }, []);

  const getStatusBadge = (status: ChoreStatus) => {
    let color = 'gray';
    switch (status) {
      case 'approved':
        color = 'green';
        break;
      case 'pending_approval':
        color = 'yellow';
        break;
      case 'rejected':
        color = 'red';
        break;
    }
    return <Badge color={color} variant="light">{status.replace('_', ' ').toUpperCase()}</Badge>;
  };

  if (isLoading) {
    return (
      <Container size="md" py="xl" style={{ display: 'flex', justifyContent: 'center' }}>
        <Loader />
      </Container>
    );
  }

  const columns = [
    {
      key: 'chore_name',
      label: 'Chore Name',
      render: (value: string) => <Text fw={500}>{value}</Text>
    },
    {
      key: 'points_value',
      label: 'Points',
      align: 'right' as const,
      render: (value: number, row: ChoreLogWithStreakBonus) => (
        <Group gap="xs" justify="flex-end">
          <Text>{value}</Text>
          {row.streak_bonus_points && (
            <Tooltip label={`${row.streak_day}-day streak bonus!`}>
              <Group gap={4}>
                <IconFlame size={16} color="orange" />
                <Text fw={700} c="orange">+{row.streak_bonus_points}</Text>
              </Group>
            </Tooltip>
          )}
        </Group>
      )
    },
    {
      key: 'status',
      label: 'Status',
      render: (value: ChoreStatus) => getStatusBadge(value)
    },
    {
      key: 'submitted_at',
      label: 'Submitted At',
      render: (value: string) => <Text size="sm">{new Date(value).toLocaleString()}</Text>
    },
    {
      key: 'reviewed_at',
      label: 'Reviewed At',
      render: (value: string | null) => (
        <Text size="sm">{value ? new Date(value).toLocaleString() : '-'}</Text>
      )
    }
  ];

  const cardRender = (log: ChoreLogWithStreakBonus) => (
    <Stack gap="sm">
      <Group justify="space-between">
        <Text fw={600} size="lg">{log.chore_name}</Text>
        {getStatusBadge(log.status)}
      </Group>
      
      <Group justify="space-between">
        <Group gap="xs">
          <IconCoins size={18} />
          <Text fw={500}>
            {log.points_value} points
            {log.streak_bonus_points && (
              <Text component="span" c="orange" fw={700} ml="xs">
                +{log.streak_bonus_points} bonus
              </Text>
            )}
          </Text>
        </Group>
        {log.streak_bonus_points && (
          <Tooltip label={`${log.streak_day}-day streak!`}>
            <Badge color="orange" leftSection={<IconFlame size={14} />}>
              Day {log.streak_day}
            </Badge>
          </Tooltip>
        )}
      </Group>
      
      <Group gap="xs" c="dimmed">
        <IconCalendar size={16} />
        <Text size="sm">
          {new Date(log.submitted_at).toLocaleDateString()} at {new Date(log.submitted_at).toLocaleTimeString()}
        </Text>
      </Group>
      
      {log.reviewed_at && (
        <Text size="sm" c="dimmed">
          Reviewed: {new Date(log.reviewed_at).toLocaleDateString()}
        </Text>
      )}
    </Stack>
  );

  return (
    <Container size="lg" py="xl">
      <Stack gap="lg">
        <Title order={2} ta="center">
          My Chore History
        </Title>

        {error && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" withCloseButton onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {choreHistory.length === 0 && !isLoading && (
          <Paper p="lg" shadow="xs" withBorder>
            <Text ta="center">You haven't submitted any chores yet.</Text>
          </Paper>
        )}

        {choreHistory.length > 0 && (
          <>
            {/* Streak Bonus Summary */}
            {(() => {
              const totalStreakBonus = choreHistory.reduce((sum, log) => sum + (log.streak_bonus_points || 0), 0);
              const streakMilestones = choreHistory.filter(log => log.streak_bonus_points).length;
              
              return totalStreakBonus > 0 ? (
                <Paper p="md" shadow="xs" withBorder>
                  <Group justify="space-between">
                    <Group gap="xs">
                      <IconFlame size={20} color="orange" />
                      <Text fw={500}>Streak Bonuses Earned</Text>
                    </Group>
                    <Group gap="lg">
                      <Text size="sm" c="dimmed">
                        {streakMilestones} milestone{streakMilestones !== 1 ? 's' : ''} reached
                      </Text>
                      <Badge size="lg" color="orange" variant="filled">
                        +{totalStreakBonus} bonus points
                      </Badge>
                    </Group>
                  </Group>
                </Paper>
              ) : null;
            })()}

            <ResponsiveTable
              data={choreHistory}
              columns={columns}
              cardRender={cardRender}
              className="fade-in"
            />
          </>
        )}
      </Stack>
    </Container>
  );
};

export default ChoreHistoryPage;
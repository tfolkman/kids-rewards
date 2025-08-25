import React, { useState, useEffect, useMemo } from 'react';
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
  SimpleGrid,
  ThemeIcon,
  Progress,
} from '@mantine/core';
import { 
  IconAlertCircle, 
  IconFlame, 
  IconCalendar, 
  IconCoins,
  IconClock,
  IconRefresh,
  IconTrophy,
  IconTarget
} from '@tabler/icons-react';
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

  // Calculate effort statistics
  const effortStats = useMemo(() => {
    const totalEffortMinutes = choreHistory.reduce((sum, log) => sum + (log.effort_minutes || 0), 0);
    const totalEffortPoints = choreHistory.reduce((sum, log) => sum + (log.effort_points || 0), 0);
    const retryAttempts = choreHistory.filter(log => log.is_retry).length;
    const highEffortChores = choreHistory.filter(log => (log.effort_minutes || 0) >= 10).length;
    const averageEffort = choreHistory.length > 0 
      ? Math.round(totalEffortMinutes / choreHistory.length) 
      : 0;
    
    return {
      totalMinutes: totalEffortMinutes,
      totalPoints: totalEffortPoints,
      retryCount: retryAttempts,
      highEffortCount: highEffortChores,
      averageMinutes: averageEffort,
      totalChores: choreHistory.length
    };
  }, [choreHistory]);

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
      render: (value: string, row: ChoreLogWithStreakBonus) => (
        <Stack gap={2}>
          <Text fw={500}>{value}</Text>
          {row.is_retry && (
            <Badge size="xs" color="orange" leftSection={<IconRefresh size={10} />}>
              Retry Attempt
            </Badge>
          )}
        </Stack>
      )
    },
    {
      key: 'effort',
      label: 'Effort',
      render: (_: any, row: ChoreLogWithStreakBonus) => {
        if (!row.effort_minutes) return <Text size="sm" c="dimmed">-</Text>;
        return (
          <Stack gap={2}>
            <Group gap={4}>
              <IconClock size={14} />
              <Text size="sm">{row.effort_minutes} min</Text>
            </Group>
            {row.effort_points && row.effort_points > 0 && (
              <Text size="xs" c="teal">+{row.effort_points} effort pts</Text>
            )}
          </Stack>
        );
      }
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
      label: 'Submitted',
      render: (value: string) => <Text size="sm">{new Date(value).toLocaleDateString()}</Text>
    }
  ];

  const cardRender = (log: ChoreLogWithStreakBonus) => (
    <Stack gap="sm">
      <Group justify="space-between">
        <Stack gap={2}>
          <Text fw={600} size="lg">{log.chore_name}</Text>
          {log.is_retry && (
            <Badge size="xs" color="orange" leftSection={<IconRefresh size={10} />}>
              Retry Attempt
            </Badge>
          )}
        </Stack>
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
      
      {log.effort_minutes && log.effort_minutes > 0 && (
        <Group gap="xs">
          <IconClock size={16} />
          <Text size="sm">
            {log.effort_minutes} min effort
            {log.effort_points && log.effort_points > 0 && (
              <Text component="span" c="teal" fw={500}>
                {' '}(+{log.effort_points} pts)
              </Text>
            )}
          </Text>
        </Group>
      )}
      
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

        {/* Effort Statistics Cards */}
        {choreHistory.length > 0 && (
          <SimpleGrid cols={{ base: 1, sm: 2, md: 4 }} spacing="md">
            <Card padding="lg" radius="md" withBorder>
              <Group justify="space-between">
                <div>
                  <Text size="xs" c="dimmed" fw={700} tt="uppercase">
                    Total Effort
                  </Text>
                  <Text size="xl" fw={700}>
                    {effortStats.totalMinutes} min
                  </Text>
                  <Text size="xs" c="teal">
                    {effortStats.totalPoints} effort points earned
                  </Text>
                </div>
                <ThemeIcon color="blue" size="xl" radius="md" variant="light">
                  <IconClock size={28} />
                </ThemeIcon>
              </Group>
            </Card>

            <Card padding="lg" radius="md" withBorder>
              <Group justify="space-between">
                <div>
                  <Text size="xs" c="dimmed" fw={700} tt="uppercase">
                    Average Effort
                  </Text>
                  <Text size="xl" fw={700}>
                    {effortStats.averageMinutes} min
                  </Text>
                  <Text size="xs" c="dimmed">
                    per chore
                  </Text>
                </div>
                <ThemeIcon color="teal" size="xl" radius="md" variant="light">
                  <IconTarget size={28} />
                </ThemeIcon>
              </Group>
            </Card>

            <Card padding="lg" radius="md" withBorder>
              <Group justify="space-between">
                <div>
                  <Text size="xs" c="dimmed" fw={700} tt="uppercase">
                    Persistence
                  </Text>
                  <Text size="xl" fw={700}>
                    {effortStats.retryCount}
                  </Text>
                  <Text size="xs" c="orange">
                    retry attempts
                  </Text>
                </div>
                <ThemeIcon color="orange" size="xl" radius="md" variant="light">
                  <IconRefresh size={28} />
                </ThemeIcon>
              </Group>
            </Card>

            <Card padding="lg" radius="md" withBorder>
              <Group justify="space-between">
                <div>
                  <Text size="xs" c="dimmed" fw={700} tt="uppercase">
                    High Effort
                  </Text>
                  <Text size="xl" fw={700}>
                    {effortStats.highEffortCount}
                  </Text>
                  <Text size="xs" c="grape">
                    10+ min chores
                  </Text>
                </div>
                <ThemeIcon color="grape" size="xl" radius="md" variant="light">
                  <IconTrophy size={28} />
                </ThemeIcon>
              </Group>
            </Card>
          </SimpleGrid>
        )}

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
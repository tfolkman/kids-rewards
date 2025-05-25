import React, { useState, useEffect } from 'react';
import * as api from '../services/api';
import { ChoreLogWithStreakBonus, ChoreStatus } from '../services/api';
import {
  Table,
  Text,
  Paper,
  Loader,
  Alert,
  Title,
  Container,
  Stack,
  Badge,
  ScrollArea,
  Group,
  Tooltip,
} from '@mantine/core';
import { IconAlertCircle, IconFlame } from '@tabler/icons-react';

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

  const rows = choreHistory.map((log) => (
    <Table.Tr key={log.id}>
      <Table.Td>
        <Text fw={500}>{log.chore_name}</Text>
      </Table.Td>
      <Table.Td ta="right">
        <Group gap="xs" justify="flex-end">
          <Text>{log.points_value}</Text>
          {log.streak_bonus_points && (
            <Tooltip label={`${log.streak_day}-day streak bonus!`}>
              <Group gap={4}>
                <IconFlame size={16} color="orange" />
                <Text fw={700} c="orange">+{log.streak_bonus_points}</Text>
              </Group>
            </Tooltip>
          )}
        </Group>
      </Table.Td>
      <Table.Td>{getStatusBadge(log.status)}</Table.Td>
      <Table.Td>
        <Text fz="sm">{new Date(log.submitted_at).toLocaleString()}</Text>
      </Table.Td>
      <Table.Td>
        <Text fz="sm">
          {log.reviewed_at ? new Date(log.reviewed_at).toLocaleString() : '-'}
        </Text>
      </Table.Td>
    </Table.Tr>
  ));

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

            <Paper shadow="md" radius="md" withBorder>
              <ScrollArea>
                <Table striped highlightOnHover withTableBorder withColumnBorders verticalSpacing="sm" horizontalSpacing="md" miw={700}>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Chore Name</Table.Th>
                      <Table.Th ta="right">Points</Table.Th>
                      <Table.Th>Status</Table.Th>
                      <Table.Th>Submitted At</Table.Th>
                      <Table.Th>Reviewed At</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>{rows}</Table.Tbody>
                </Table>
              </ScrollArea>
            </Paper>
          </>
        )}
      </Stack>
    </Container>
  );
};

export default ChoreHistoryPage;
import React, { useState, useEffect } from 'react';
import * as api from '../services/api';
import { ChoreLog, ChoreStatus } from '../services/api';
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
} from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';

const ChoreHistoryPage: React.FC = () => {
  const [choreHistory, setChoreHistory] = useState<ChoreLog[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchChoreHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.getMyChoreHistory();
      // Sort by submitted_at date, newest first
      const sortedHistory = response.data.sort((a, b) => new Date(b.submitted_at).getTime() - new Date(a.submitted_at).getTime());
      setChoreHistory(sortedHistory);
    } catch (err) {
      setError('Failed to fetch chore history. Please try again.');
      console.error(err);
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
      <Table.Td ta="right">{log.points_value}</Table.Td>
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
        )}
      </Stack>
    </Container>
  );
};

export default ChoreHistoryPage;
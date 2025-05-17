import React, { useState, useEffect } from 'react';
import { Container, Title, Table, Text, LoadingOverlay, Alert, Paper, Badge, Group } from '@mantine/core';
import { IconAlertCircle, IconReceipt } from '@tabler/icons-react';
import { getMyPurchaseHistory } from '../services/api';
import type { PurchaseLog } from '../services/api';
import { useAuth } from '../App'; // To ensure user is logged in

const PurchaseHistoryPage = () => {
  const [history, setHistory] = useState<PurchaseLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { currentUser } = useAuth();

  useEffect(() => {
    if (!currentUser) {
      setError("You must be logged in to view purchase history.");
      setLoading(false);
      return;
    }

    const fetchHistory = async () => {
      try {
        setLoading(true);
        const response = await getMyPurchaseHistory();
        setHistory(response.data);
        setError(null);
      } catch (err) {
        setError('Failed to load purchase history.');
        console.error('Error fetching purchase history:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [currentUser]);

  if (loading) return <LoadingOverlay visible />;

  return (
    <Container size="lg" my="xl">
      <Paper shadow="sm" p="lg" radius="md" withBorder>
        <Group mb="xl">
          <IconReceipt size={32} />
          <Title order={1}>Purchase History</Title>
        </Group>

        {error && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" radius="md" mb="lg">
            {error}
          </Alert>
        )}

        {!loading && !error && history.length === 0 && (
          <Text ta="center" c="dimmed" py="xl">
            You haven't made any purchases yet.
          </Text>
        )}

        {!loading && !error && history.length > 0 && (
          <Table striped highlightOnHover verticalSpacing="sm">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Date</Table.Th>
                <Table.Th>Item</Table.Th>
                <Table.Th ta="right">Points Spent</Table.Th>
                <Table.Th>Status</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {history.map((log) => (
                <Table.Tr key={log.id}>
                  <Table.Td>{new Date(log.timestamp).toLocaleDateString()}</Table.Td>
                  <Table.Td>{log.item_name}</Table.Td>
                  <Table.Td ta="right">
                    <Badge color="yellow" variant="light">
                      {log.points_spent}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Badge 
                      color={
                        log.status === 'completed' ? 'green' :
                        log.status === 'pending' ? 'blue' :
                        log.status === 'approved' ? 'teal' : 
                        log.status === 'rejected' ? 'red' : 'gray'
                      }
                      variant="filled"
                    >
                      {log.status.charAt(0).toUpperCase() + log.status.slice(1)}
                    </Badge>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}
      </Paper>
    </Container>
  );
};

export default PurchaseHistoryPage;
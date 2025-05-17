import React, { useState, useEffect, useCallback } from 'react';
import { Container, Title, Table, Text, LoadingOverlay, Alert, Paper, Button, Group, Badge, Stack } from '@mantine/core';
import { IconAlertCircle, IconChecks, IconX, IconHourglassHigh } from '@tabler/icons-react';
import { getPendingPurchaseRequests, approvePurchaseRequest, rejectPurchaseRequest } from '../services/api';
import type { PurchaseLog } from '../services/api';
import { useAuth } from '../App';

const PendingRequestsPage = () => {
  const [requests, setRequests] = useState<PurchaseLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({}); // For individual row loading
  const { currentUser } = useAuth();

  const fetchRequests = useCallback(async () => {
    if (currentUser?.role !== 'parent') {
      setError("You must be a parent to view pending requests.");
      setLoading(false);
      setRequests([]);
      return;
    }
    try {
      setLoading(true);
      const response = await getPendingPurchaseRequests();
      setRequests(response.data);
      setError(null);
    } catch (err) {
      setError('Failed to load pending requests.');
      console.error('Error fetching pending requests:', err);
    } finally {
      setLoading(false);
    }
  }, [currentUser]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const handleAction = async (logId: string, action: 'approve' | 'reject') => {
    setActionLoading(prev => ({ ...prev, [logId]: true }));
    try {
      if (action === 'approve') {
        await approvePurchaseRequest({ log_id: logId });
      } else {
        await rejectPurchaseRequest({ log_id: logId });
      }
      // Refresh the list after action
      fetchRequests(); 
      // TODO: Consider more targeted state update instead of full refetch for better UX
      // For example, removing the item from the list or updating its status locally.
    } catch (err: any) {
      setError(`Failed to ${action} request: ${err.response?.data?.detail || err.message}`);
      console.error(`Error ${action}ing request:`, err);
    } finally {
      setActionLoading(prev => ({ ...prev, [logId]: false }));
    }
  };

  if (loading) return <LoadingOverlay visible />;

  if (currentUser?.role !== 'parent' && !loading) {
     return (
        <Container size="md" my="xl">
            <Alert icon={<IconAlertCircle size="1rem" />} title="Access Denied" color="red" radius="md">
                You do not have permission to view this page.
            </Alert>
        </Container>
     );
  }


  return (
    <Container size="lg" my="xl">
      <Paper shadow="sm" p="lg" radius="md" withBorder>
        <Group mb="xl">
          <IconHourglassHigh size={32} />
          <Title order={1}>Pending Purchase Requests</Title>
        </Group>

        {error && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" radius="md" mb="lg">
            {error}
          </Alert>
        )}

        {!loading && !error && requests.length === 0 && (
          <Text ta="center" c="dimmed" py="xl">
            There are no pending purchase requests at this time.
          </Text>
        )}

        {!loading && !error && requests.length > 0 && (
          <Table striped highlightOnHover verticalSpacing="sm">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Date</Table.Th>
                <Table.Th>Kid</Table.Th>
                <Table.Th>Item</Table.Th>
                <Table.Th ta="right">Points</Table.Th>
                <Table.Th ta="center">Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {requests.map((log) => (
                <Table.Tr key={log.id}>
                  <Table.Td>{new Date(log.timestamp).toLocaleDateString()}</Table.Td>
                  <Table.Td>{log.username}</Table.Td>
                  <Table.Td>{log.item_name}</Table.Td>
                  <Table.Td ta="right">
                    <Badge color="yellow" variant="light">
                      {log.points_spent}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Group justify="center">
                      <Button
                        size="xs"
                        color="green"
                        onClick={() => handleAction(log.id, 'approve')}
                        loading={actionLoading[log.id]}
                        disabled={actionLoading[log.id]}
                        leftSection={<IconChecks size={16}/>}
                      >
                        Approve
                      </Button>
                      <Button
                        size="xs"
                        color="red"
                        onClick={() => handleAction(log.id, 'reject')}
                        loading={actionLoading[log.id]}
                        disabled={actionLoading[log.id]}
                        leftSection={<IconX size={16}/>}
                      >
                        Reject
                      </Button>
                    </Group>
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

export default PendingRequestsPage;
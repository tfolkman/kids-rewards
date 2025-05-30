import React, { useState, useEffect, useCallback } from 'react';
import { Container, Title, Table, Text, LoadingOverlay, Alert, Paper, Button, Group, Badge, Stack } from '@mantine/core';
import { IconAlertCircle, IconChecks, IconX, IconHourglassHigh, IconClipboardCheck, IconShoppingCart, IconPlus, IconListDetails } from '@tabler/icons-react'; // Added IconShoppingCart, IconPlus, IconListDetails
import {
    getPendingPurchaseRequests,
    approvePurchaseRequest,
    rejectPurchaseRequest,
    getPendingChoreSubmissionsForMyChores,
    approveChoreSubmission,
    rejectChoreSubmission,
    getPendingFeatureRequests, // Added
    approveFeatureRequest,    // Added
    rejectFeatureRequest,     // Added
    FeatureRequestAPI         // Added
} from '../services/api';
import type { PurchaseLog, ChoreLog } from '../services/api'; // Added ChoreLog
import { useAuth } from '../App';

const PendingRequestsPage = () => {
  const [purchaseRequests, setPurchaseRequests] = useState<PurchaseLog[]>([]);
  const [choreSubmissions, setChoreSubmissions] = useState<ChoreLog[]>([]);
  const [featureRequests, setFeatureRequests] = useState<FeatureRequestAPI[]>([]); // Added
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({}); // For individual row loading
  const { currentUser } = useAuth();

  const fetchAllPendingRequests = useCallback(async () => {
    if (currentUser?.role !== 'parent') {
      setError("You must be a parent to view pending requests.");
      setLoading(false);
      setPurchaseRequests([]);
      setChoreSubmissions([]);
      setFeatureRequests([]); // Added
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [purchaseRes, choreRes, featureRes] = await Promise.all([ // Added featureRes
        getPendingPurchaseRequests(),
        getPendingChoreSubmissionsForMyChores(),
        getPendingFeatureRequests() // Added
      ]);
      // Filter for pending items only
      setPurchaseRequests(purchaseRes.data.filter(p => p.status === 'pending'));
      setChoreSubmissions(choreRes.data.filter(c => c.status === 'pending_approval'));
      setFeatureRequests(featureRes.data.filter(r => r.status === 'pending'));
    } catch (err) {
      setError('Failed to load pending requests. Please try again.');
      console.error('Error fetching pending requests:', err);
      setPurchaseRequests([]);
      setChoreSubmissions([]);
      setFeatureRequests([]); // Added
    } finally {
      setLoading(false);
    }
  }, [currentUser]);

  useEffect(() => {
    fetchAllPendingRequests();
  }, [fetchAllPendingRequests]);

  const handleAction = async (id: string, action: 'approve' | 'reject', type: 'purchase' | 'chore' | 'feature_request') => {
    setActionLoading(prev => ({ ...prev, [id]: true }));
    setError(null);
    try {
      if (type === 'purchase') {
        if (action === 'approve') {
          await approvePurchaseRequest({ log_id: id });
        } else {
          await rejectPurchaseRequest({ log_id: id });
        }
      } else if (type === 'chore') {
        if (action === 'approve') {
          await approveChoreSubmission({ chore_log_id: id });
        } else {
          await rejectChoreSubmission({ chore_log_id: id });
        }
      } else if (type === 'feature_request') { // Added
        if (action === 'approve') {
          await approveFeatureRequest(id);
        } else {
          await rejectFeatureRequest(id);
        }
      }
      fetchAllPendingRequests(); // Refresh all lists
    } catch (err: any) {
      setError(`Failed to ${action} ${type.replace('_', ' ')}: ${err.response?.data?.detail || err.message}`);
      console.error(`Error ${action}ing ${type.replace('_', ' ')}:`, err);
    } finally {
      setActionLoading(prev => ({ ...prev, [id]: false }));
    }
  };

  if (loading && !purchaseRequests.length && !choreSubmissions.length && !featureRequests.length) return <LoadingOverlay visible />; // Added featureRequests.length

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
        <Group mb="xl" align="center">
          <IconHourglassHigh size={36} stroke={1.5} />
          <Title order={1}>Pending Requests</Title>
        </Group>

        {error && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" radius="md" mb="lg" onClose={() => setError(null)} withCloseButton>
            {error}
          </Alert>
        )}

        {/* Purchase Requests Table */}
        <Title order={2} mt="xl" mb="md" c="blue.7">
            <Group><IconShoppingCart size={24}/> Pending Item Redemptions</Group>
        </Title>
        {loading && purchaseRequests.length === 0 && <Text>Loading purchase requests...</Text>}
        {!loading && purchaseRequests.length === 0 && (
          <Text ta="center" c="dimmed" py="md">
            No pending item redemptions.
          </Text>
        )}
        {purchaseRequests.length > 0 && (
          <Table striped highlightOnHover verticalSpacing="sm" mt="md">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Date</Table.Th>
                <Table.Th>Kid</Table.Th>
                <Table.Th>Item</Table.Th>
                <Table.Th ta="right">Points Cost</Table.Th>
                <Table.Th ta="center">Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {purchaseRequests.map((log) => (
                <Table.Tr key={`purchase-${log.id}`}>
                  <Table.Td>{new Date(log.timestamp).toLocaleDateString()}</Table.Td>
                  <Table.Td>{log.username}</Table.Td>
                  <Table.Td>{log.item_name}</Table.Td>
                  <Table.Td ta="right">
                    <Badge color="orange" variant="light">
                      {log.points_spent}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Group justify="center">
                      <Button
                        size="xs"
                        color="green"
                        onClick={() => handleAction(log.id, 'approve', 'purchase')}
                        loading={actionLoading[log.id]}
                        disabled={actionLoading[log.id]}
                        leftSection={<IconChecks size={16}/>}
                      >
                        Approve
                      </Button>
                      <Button
                        size="xs"
                        color="red"
                        onClick={() => handleAction(log.id, 'reject', 'purchase')}
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

        {/* Chore Submissions Table */}
        <Title order={2} mt="xxl" mb="md" c="teal.7">
            <Group><IconClipboardCheck size={24}/> Pending Chore Submissions</Group>
        </Title>
        {loading && choreSubmissions.length === 0 && <Text>Loading chore submissions...</Text>}
        {!loading && choreSubmissions.length === 0 && (
          <Text ta="center" c="dimmed" py="md">
            No pending chore submissions.
          </Text>
        )}
        {choreSubmissions.length > 0 && (
          <Table striped highlightOnHover verticalSpacing="sm" mt="md">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Submitted</Table.Th>
                <Table.Th>Kid</Table.Th>
                <Table.Th>Chore</Table.Th>
                <Table.Th ta="right">Points Value</Table.Th>
                <Table.Th ta="center">Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {choreSubmissions.map((log) => (
                <Table.Tr key={`chore-${log.id}`}>
                  <Table.Td>{new Date(log.submitted_at).toLocaleDateString()}</Table.Td>
                  <Table.Td>{log.kid_username}</Table.Td>
                  <Table.Td>{log.chore_name}</Table.Td>
                  <Table.Td ta="right">
                    <Badge color="green" variant="light">
                      {log.points_value}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Group justify="center">
                      <Button
                        size="xs"
                        color="green"
                        onClick={() => handleAction(log.id, 'approve', 'chore')}
                        loading={actionLoading[log.id]}
                        disabled={actionLoading[log.id]}
                        leftSection={<IconChecks size={16}/>}
                      >
                        Approve
                      </Button>
                      <Button
                        size="xs"
                        color="red"
                        onClick={() => handleAction(log.id, 'reject', 'chore')}
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

        {/* Feature Requests Table */}
        <Title order={2} mt="xxl" mb="md" c="violet.7">
            <Group><IconPlus size={24}/> Pending Feature Requests</Group>
        </Title>
        {loading && featureRequests.length === 0 && <Text>Loading feature requests...</Text>}
        {!loading && featureRequests.length === 0 && (
          <Text ta="center" c="dimmed" py="md">
            No pending feature requests.
          </Text>
        )}
        {featureRequests.length > 0 && (
          <Table striped highlightOnHover verticalSpacing="sm" mt="md">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Date</Table.Th>
                <Table.Th>Kid</Table.Th>
                <Table.Th>Type</Table.Th>
                <Table.Th>Details</Table.Th>
                <Table.Th ta="center">Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {featureRequests.map((req) => (
                <Table.Tr key={`feature-${req.id}`}>
                  <Table.Td>{new Date(req.created_at).toLocaleDateString()}</Table.Td>
                  <Table.Td>{req.requester_username}</Table.Td>
                  <Table.Td>
                    <Badge
                      color={
                        req.request_type === 'add_store_item' ? 'blue' :
                        req.request_type === 'add_chore' ? 'cyan' : 'gray'
                      }
                      variant="light"
                    >
                      {req.request_type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Stack gap="xs">
                      {req.details.name && <Text size="sm"><strong>Name:</strong> {req.details.name}</Text>}
                      {req.details.description && <Text size="sm" c="dimmed"><strong>Desc:</strong> {req.details.description}</Text>}
                      {req.details.points_cost !== undefined && <Text size="sm"><strong>Cost:</strong> {req.details.points_cost} pts</Text>}
                      {req.details.points_value !== undefined && <Text size="sm"><strong>Value:</strong> {req.details.points_value} pts</Text>}
                      {req.details.message && <Text size="sm"><strong>Message:</strong> {req.details.message}</Text>}
                    </Stack>
                  </Table.Td>
                  <Table.Td>
                    <Group justify="center">
                      <Button
                        size="xs"
                        color="green"
                        onClick={() => handleAction(req.id, 'approve', 'feature_request')}
                        loading={actionLoading[req.id]}
                        disabled={actionLoading[req.id]}
                        leftSection={<IconChecks size={16}/>}
                      >
                        Approve
                      </Button>
                      <Button
                        size="xs"
                        color="red"
                        onClick={() => handleAction(req.id, 'reject', 'feature_request')}
                        loading={actionLoading[req.id]}
                        disabled={actionLoading[req.id]}
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
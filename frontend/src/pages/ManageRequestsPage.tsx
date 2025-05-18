import React, { useState, useEffect, useCallback } from 'react';
import {
  Container,
  Title,
  Table,
  Button,
  Group,
  Paper,
  LoadingOverlay,
  Alert,
  Text,
  Badge,
  Modal,
  Box,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconCircleCheck, IconAlertCircle, IconInfoCircle } from '@tabler/icons-react';
// We will create these API functions later
import { getPendingFeatureRequests, approveFeatureRequest, rejectFeatureRequest, FeatureRequestAPI as FeatureRequest, RequestTypeAPI as RequestType } from '../services/api'; // Updated imports

// Matches backend models.RequestType and models.RequestStatus
// enum RequestType is now imported from '../services/api.ts' and aliased as RequestType.

// enum RequestStatus { // Status will come from FeatureRequestAPI type
//   PENDING = "pending",
//   APPROVED = "approved",
//   REJECTED = "rejected",
// }

// interface RequestDetails { // Details will come from FeatureRequestAPI type
//   name?: string;
//   description?: string;
//   points_cost?: number;
//   points_value?: number;
//   message?: string;
// }

// interface FeatureRequest { // Now imported as FeatureRequestAPI and aliased
//   id: string;
//   requester_username: string;
//   request_type: RequestType;
//   details: RequestDetails;
//   status: RequestStatus;
//   created_at: string; // ISO string
// }

const ManageRequestsPage: React.FC = () => {
  const [requests, setRequests] = useState<FeatureRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processingRequestId, setProcessingRequestId] = useState<string | null>(null);
  const [selectedRequestDetails, setSelectedRequestDetails] = useState<FeatureRequest | null>(null);

  const fetchRequests = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // TODO: Replace with actual API call
      console.log('Fetching pending requests...');
      const response = await getPendingFeatureRequests();
      // Dummy data for now:
      // const dummyData: FeatureRequest[] = [
      //   { id: 'req1', requester_username: 'KidOne', request_type: RequestType.ADD_STORE_ITEM, details: { name: 'New Toy Car', description: 'A very fast toy car', points_cost: 150 }, status: "pending", created_at: new Date().toISOString() },
      //   { id: 'req2', requester_username: 'KidTwo', request_type: RequestType.ADD_CHORE, details: { name: 'Wash Dishes', description: 'Wash all dishes after dinner', points_value: 20 }, status: "pending", created_at: new Date().toISOString() },
      //   { id: 'req3', requester_username: 'KidOne', request_type: RequestType.OTHER, details: { message: 'Can we get a pet fish?' }, status: "pending", created_at: new Date().toISOString() },
      // ];
      // setRequests(dummyData);
      setRequests(response.data);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to fetch requests.';
      setError(errorMessage);
      notifications.show({
        title: 'Fetch Failed',
        message: errorMessage,
        color: 'red',
        icon: <IconAlertCircle />,
      });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const handleAction = async (requestId: string, action: 'approve' | 'reject') => {
    setProcessingRequestId(requestId);
    setError(null);
    try {
      // TODO: Replace with actual API calls
      if (action === 'approve') {
        await approveFeatureRequest(requestId);
        console.log(`Approving request ${requestId}`);
      } else {
        await rejectFeatureRequest(requestId);
        console.log(`Rejecting request ${requestId}`);
      }
      notifications.show({
        title: `Request ${action === 'approve' ? 'Approved' : 'Rejected'}`,
        message: `The request has been successfully ${action === 'approve' ? 'approved' : 'rejected'}.`,
        color: 'teal',
        icon: <IconCircleCheck />,
      });
      fetchRequests(); // Refresh the list
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || `Failed to ${action} request.`;
      setError(errorMessage);
      notifications.show({
        title: `${action === 'approve' ? 'Approval' : 'Rejection'} Failed`,
        message: errorMessage,
        color: 'red',
        icon: <IconAlertCircle />,
      });
    } finally {
      setProcessingRequestId(null);
    }
  };

  const renderRequestDetails = (request: FeatureRequest) => {
    const { details, request_type } = request;
    switch (request_type) {
      case RequestType.ADD_STORE_ITEM:
        return (
          <>
            <Text><strong>Item Name:</strong> {details.name || 'N/A'}</Text>
            <Text><strong>Description:</strong> {details.description || 'N/A'}</Text>
            <Text><strong>Points Cost:</strong> {details.points_cost || 'N/A'}</Text>
          </>
        );
      case RequestType.ADD_CHORE:
        return (
          <>
            <Text><strong>Chore Name:</strong> {details.name || 'N/A'}</Text>
            <Text><strong>Description:</strong> {details.description || 'N/A'}</Text>
            <Text><strong>Points Value:</strong> {details.points_value || 'N/A'}</Text>
          </>
        );
      case RequestType.OTHER:
        return <Text><strong>Message:</strong> {details.message || 'N/A'}</Text>;
      default:
        return <Text>No details available.</Text>;
    }
  };
  
  const rows = requests.map((request) => (
    <Table.Tr key={request.id}>
      <Table.Td>{request.requester_username}</Table.Td>
      <Table.Td>
        <Badge
          color={
            request.request_type === RequestType.ADD_CHORE ? 'blue' :
            request.request_type === RequestType.ADD_STORE_ITEM ? 'grape' : 'gray'
          }
          variant="light"
        >
          {request.request_type.replace('_', ' ').toUpperCase()}
        </Badge>
      </Table.Td>
      <Table.Td>
        <Button size="xs" variant="outline" onClick={() => setSelectedRequestDetails(request)}>
            View Details
        </Button>
      </Table.Td>
      <Table.Td>{new Date(request.created_at).toLocaleDateString()}</Table.Td>
      <Table.Td>
        <Group gap="xs">
          <Button
            size="xs"
            color="green"
            onClick={() => handleAction(request.id, 'approve')}
            loading={processingRequestId === request.id}
            disabled={!!processingRequestId && processingRequestId !== request.id}
          >
            Approve
          </Button>
          <Button
            size="xs"
            color="red"
            onClick={() => handleAction(request.id, 'reject')}
            loading={processingRequestId === request.id}
            disabled={!!processingRequestId && processingRequestId !== request.id}
          >
            Reject
          </Button>
        </Group>
      </Table.Td>
    </Table.Tr>
  ));

  return (
    <Container size="lg">
      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <Title order={2} ta="center" mb="xl">
          Manage Feature Requests
        </Title>
        <LoadingOverlay visible={loading && !error} /> {/* Show loading only if no error initially */}
        {error && (
          <Alert title="Error" color="red" withCloseButton onClose={() => setError(null)} mb="md">
            {error}
          </Alert>
        )}
        {!loading && requests.length === 0 && !error && (
          <Text ta="center" c="dimmed">No pending requests found.</Text>
        )}
        {!loading && requests.length > 0 && (
          <Table striped highlightOnHover withTableBorder withColumnBorders>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Requested By</Table.Th>
                <Table.Th>Type</Table.Th>
                <Table.Th>Details</Table.Th>
                <Table.Th>Date</Table.Th>
                <Table.Th>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>{rows}</Table.Tbody>
          </Table>
        )}
      </Paper>

      <Modal
        opened={selectedRequestDetails !== null}
        onClose={() => setSelectedRequestDetails(null)}
        title="Request Details"
        centered
      >
        {selectedRequestDetails && (
          <Box>
            <Text><strong>Requested By:</strong> {selectedRequestDetails.requester_username}</Text>
            <Text><strong>Request Type:</strong> {selectedRequestDetails.request_type.replace('_', ' ').toUpperCase()}</Text>
            <Text><strong>Date:</strong> {new Date(selectedRequestDetails.created_at).toLocaleString()}</Text>
            <hr />
            {renderRequestDetails(selectedRequestDetails)}
          </Box>
        )}
      </Modal>

    </Container>
  );
};

export default ManageRequestsPage;
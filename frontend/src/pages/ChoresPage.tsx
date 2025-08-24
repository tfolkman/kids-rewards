import React, { useState, useEffect } from 'react';
import * as api from '../services/api';
import { Chore, ChoreLog } from '../services/api'; // Assuming types are exported
import {
  Table,
  Button,
  Text,
  Paper,
  Loader,
  Alert,
  Title,
  Container,
  Stack,
  Modal,
  Group,
  Badge,
} from '@mantine/core';
import { IconAlertCircle, IconCircleCheck, IconRefresh } from '@tabler/icons-react';
import EffortTimer from '../components/EffortTimer';

const ChoresPage: React.FC = () => {
  const [availableChores, setAvailableChores] = useState<Chore[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState<string | null>(null); // Store chore ID being submitted
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [selectedChoreId, setSelectedChoreId] = useState<string | null>(null);
  const [effortMinutes, setEffortMinutes] = useState(0);
  const [choreHistory, setChoreHistory] = useState<ChoreLog[]>([]);
  const [isRetryAttempt, setIsRetryAttempt] = useState(false);

  const fetchAvailableChores = async () => {
    setIsLoading(true);
    setError(null);
    setSuccessMessage(null);
    try {
      const response = await api.getAvailableChores();
      setAvailableChores(response.data.filter(chore => chore.is_active));
    } catch (err) {
      setError('Failed to fetch available chores. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchChoreHistory = async () => {
    try {
      const response = await api.getMyChoreHistory();
      setChoreHistory(response.data);
    } catch (err) {
      console.error('Failed to fetch chore history:', err);
    }
  };

  useEffect(() => {
    fetchAvailableChores();
    fetchChoreHistory();
  }, []);

  const openConfirmationModal = (choreId: string) => {
    setSelectedChoreId(choreId);
    setEffortMinutes(0); // Reset effort timer
    
    // Check if this is a retry attempt (rejected or pending within last 24 hours)
    const now = new Date();
    const twentyFourHoursAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    
    const isRetry = choreHistory.some(log => 
      log.chore_id === choreId && 
      new Date(log.submitted_at) > twentyFourHoursAgo &&
      (log.status === 'rejected' || log.status === 'pending_approval')
    );
    
    setIsRetryAttempt(isRetry);
    setConfirmModalOpen(true);
  };

  const handleConfirmSubmitChore = async () => {
    if (!selectedChoreId) return;

    setIsSubmitting(selectedChoreId);
    setError(null);
    setSuccessMessage(null);
    try {
      await api.submitChoreCompletion(selectedChoreId, { effort_minutes: effortMinutes });
      
      let message = 'Chore submitted successfully! It is now pending approval.';
      if (effortMinutes >= 10) {
        message += ' Great effort! You earned effort points that count towards your streak!';
      } else if (effortMinutes > 0) {
        message += ` You earned ${Math.floor(effortMinutes * 0.5)} effort points!`;
      }
      
      setSuccessMessage(message);
      // Refresh chores and history
      fetchAvailableChores();
      fetchChoreHistory();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit chore.');
      console.error(err);
    } finally {
      setIsSubmitting(null);
      setConfirmModalOpen(false);
      setSelectedChoreId(null);
      setEffortMinutes(0);
      setIsRetryAttempt(false);
    }
  };

  if (isLoading && availableChores.length === 0) {
    return (
      <Container size="md" py="xl" style={{ display: 'flex', justifyContent: 'center' }}>
        <Loader />
      </Container>
    );
  }

  const rows = availableChores.map((chore) => (
    <Table.Tr key={chore.id}>
      <Table.Td>
        <Text fw={500}>{chore.name}</Text>
      </Table.Td>
      <Table.Td>
        <Text c="dimmed" fz="sm">
          {chore.description || '-'}
        </Text>
      </Table.Td>
      <Table.Td>
        <Text ta="right">{chore.points_value}</Text>
      </Table.Td>
      <Table.Td>
        <Button
          onClick={() => openConfirmationModal(chore.id)}
          loading={isSubmitting === chore.id}
          variant="light"
          color="green"
          fullWidth
        >
          Mark as Done
        </Button>
      </Table.Td>
    </Table.Tr>
  ));

  return (
    <Container size="lg" py="xl">
      <Stack gap="lg">
        <Title order={2} ta="center">
          Available Chores
        </Title>

        {error && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" withCloseButton onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
        {successMessage && (
          <Alert icon={<IconCircleCheck size="1rem" />} title="Success" color="green" withCloseButton onClose={() => setSuccessMessage(null)}>
            {successMessage}
          </Alert>
        )}

        {availableChores.length === 0 && !isLoading && (
          <Paper p="lg" shadow="xs" withBorder>
            <Text ta="center">No chores are currently available. Check back later!</Text>
          </Paper>
        )}

        {availableChores.length > 0 && (
          <Paper shadow="md" radius="md" withBorder>
            <Table striped highlightOnHover withTableBorder withColumnBorders verticalSpacing="sm" horizontalSpacing="md">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Chore Name</Table.Th>
                  <Table.Th>Description</Table.Th>
                  <Table.Th ta="right">Points</Table.Th>
                  <Table.Th ta="center">Action</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>{rows}</Table.Tbody>
            </Table>
          </Paper>
        )}
      </Stack>

      <Modal
        opened={confirmModalOpen}
        onClose={() => {
          setConfirmModalOpen(false);
          setEffortMinutes(0);
          setIsRetryAttempt(false);
        }}
        title={
          <Group>
            <Text fw={500}>Submit Chore</Text>
            {isRetryAttempt && (
              <Badge color="orange" variant="filled" leftSection={<IconRefresh size={14} />}>
                Retry Attempt
              </Badge>
            )}
          </Group>
        }
        centered
        size="lg"
      >
        <Stack gap="md">
          <Text>Track how long you worked on this chore to earn effort points!</Text>
          
          <EffortTimer 
            onTimeUpdate={setEffortMinutes} 
            isRetry={isRetryAttempt}
          />
          
          <Text size="sm" c="dimmed">
            Ready to submit? Make sure to stop the timer first to save your effort time.
          </Text>
          
          <Group mt="lg" justify="space-between">
            <Button 
              variant="default" 
              onClick={() => {
                setConfirmModalOpen(false);
                setEffortMinutes(0);
                setIsRetryAttempt(false);
              }}
            >
              Cancel
            </Button>
            <Button 
              color="green" 
              onClick={handleConfirmSubmitChore} 
              loading={!!isSubmitting}
              leftSection={effortMinutes > 0 ? `+${Math.min(Math.floor(effortMinutes * 0.5), 10)} pts` : undefined}
            >
              Submit Chore
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
};

export default ChoresPage;
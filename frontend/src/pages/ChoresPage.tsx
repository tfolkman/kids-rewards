import React, { useState, useEffect } from 'react';
import * as api from '../services/api';
import { Chore } from '../services/api'; // Assuming types are exported
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
} from '@mantine/core';
import { IconAlertCircle, IconCircleCheck } from '@tabler/icons-react';

const ChoresPage: React.FC = () => {
  const [availableChores, setAvailableChores] = useState<Chore[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState<string | null>(null); // Store chore ID being submitted
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [selectedChoreId, setSelectedChoreId] = useState<string | null>(null);

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

  useEffect(() => {
    fetchAvailableChores();
  }, []);

  const openConfirmationModal = (choreId: string) => {
    setSelectedChoreId(choreId);
    setConfirmModalOpen(true);
  };

  const handleConfirmSubmitChore = async () => {
    if (!selectedChoreId) return;

    setIsSubmitting(selectedChoreId);
    setError(null);
    setSuccessMessage(null);
    try {
      await api.submitChoreCompletion(selectedChoreId);
      setSuccessMessage('Chore submitted successfully! It is now pending approval.');
      // Refresh chores to remove the submitted one or update its status
      fetchAvailableChores();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit chore.');
      console.error(err);
    } finally {
      setIsSubmitting(null);
      setConfirmModalOpen(false);
      setSelectedChoreId(null);
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
        onClose={() => setConfirmModalOpen(false)}
        title="Confirm Chore Submission"
        centered
      >
        <Text>Are you sure you want to submit this chore as completed?</Text>
        <Group mt="lg">
          <Button variant="default" onClick={() => setConfirmModalOpen(false)}>
            Cancel
          </Button>
          <Button color="green" onClick={handleConfirmSubmitChore} loading={!!isSubmitting}>
            Yes, Submit
          </Button>
        </Group>
      </Modal>
    </Container>
  );
};

export default ChoresPage;
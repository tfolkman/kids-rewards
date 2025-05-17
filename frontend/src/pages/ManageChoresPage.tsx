import React, { useState, useEffect } from 'react';
import * as api from '../services/api';
import { Chore, ChoreCreate } from '../services/api';
import {
  Button,
  Modal,
  TextInput,
  Textarea,
  NumberInput,
  Table,
  Paper,
  Title,
  Container,
  Stack,
  Group,
  ActionIcon,
  Text,
  Alert,
  Loader,
  Badge,
  ScrollArea,
  Menu,
  useMantineTheme,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { IconPencil, IconTrash, IconCircleOff, IconDotsVertical, IconPlus, IconAlertCircle, IconCircleCheck } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications'; // Assuming you have notifications setup

const ManageChoresPage: React.FC = () => {
  const theme = useMantineTheme();
  const [chores, setChores] = useState<Chore[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const [modalOpened, setModalOpened] = useState(false);
  const [editingChore, setEditingChore] = useState<Chore | null>(null);

  const [confirmDeleteModalOpen, setConfirmDeleteModalOpen] = useState(false);
  const [confirmDeactivateModalOpen, setConfirmDeactivateModalOpen] = useState(false);
  const [choreToModify, setChoreToModify] = useState<Chore | null>(null);


  const form = useForm<ChoreCreate>({
    initialValues: {
      name: '',
      description: '',
      points_value: 1,
    },
    validate: {
      name: (value: string) => (value.trim().length > 0 ? null : 'Chore name is required'),
      points_value: (value: number) => (value > 0 ? null : 'Points must be greater than 0'),
    },
  });

  const fetchChores = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.getMyCreatedChores();
      setChores(response.data.sort((a,b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()));
    } catch (err) {
      setError('Failed to fetch chores. Please try again.');
      console.error(err);
      notifications.show({
        title: 'Error',
        message: 'Failed to fetch chores.',
        color: 'red',
        icon: <IconAlertCircle />,
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchChores();
  }, []);

  const handleOpenModal = (chore: Chore | null = null) => {
    setEditingChore(chore);
    if (chore) {
      form.setValues({
        name: chore.name,
        description: chore.description || '',
        points_value: chore.points_value,
      });
    } else {
      form.reset();
    }
    setModalOpened(true);
    setError(null); // Clear previous modal errors
    setSuccessMessage(null);
  };

  const handleCloseModal = () => {
    setModalOpened(false);
    setEditingChore(null);
    form.reset();
  };

  const handleSubmitChore = async (values: ChoreCreate) => {
    setIsSubmitting(true);
    setError(null);
    setSuccessMessage(null);
    try {
      if (editingChore) {
        await api.updateChore(editingChore.id, values);
        setSuccessMessage('Chore updated successfully!');
        notifications.show({
          title: 'Success',
          message: 'Chore updated successfully!',
          color: 'green',
          icon: <IconCircleCheck />,
        });
      } else {
        await api.createChore(values);
        setSuccessMessage('Chore created successfully!');
        notifications.show({
          title: 'Success',
          message: 'Chore created successfully!',
          color: 'green',
          icon: <IconCircleCheck />,
        });
      }
      fetchChores();
      handleCloseModal();
    } catch (err: any) {
      const apiError = err.response?.data?.detail || (editingChore ? 'Failed to update chore.' : 'Failed to create chore.');
      setError(apiError);
      notifications.show({
        title: 'Error',
        message: apiError,
        color: 'red',
        icon: <IconAlertCircle />,
      });
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const openDeleteConfirmModal = (chore: Chore) => {
    setChoreToModify(chore);
    setConfirmDeleteModalOpen(true);
  };

  const handleDeleteChore = async () => {
    if (!choreToModify) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await api.deleteChore(choreToModify.id);
      setSuccessMessage('Chore deleted successfully.');
      notifications.show({
        title: 'Success',
        message: 'Chore deleted successfully!',
        color: 'green',
        icon: <IconCircleCheck />,
      });
      fetchChores();
      setConfirmDeleteModalOpen(false);
      setChoreToModify(null);
    } catch (err: any) {
      const apiError = err.response?.data?.detail || 'Failed to delete chore.';
      setError(apiError);
       notifications.show({
        title: 'Error',
        message: apiError,
        color: 'red',
        icon: <IconAlertCircle />,
      });
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const openDeactivateConfirmModal = (chore: Chore) => {
    setChoreToModify(chore);
    setConfirmDeactivateModalOpen(true);
  };

  const handleDeactivateChore = async () => {
    if (!choreToModify) return;
    setIsSubmitting(true);
    setError(null);
    try {
      await api.deactivateChore(choreToModify.id);
      setSuccessMessage('Chore deactivated successfully.');
      notifications.show({
        title: 'Success',
        message: 'Chore deactivated successfully!',
        color: 'green',
        icon: <IconCircleCheck />,
      });
      fetchChores();
      setConfirmDeactivateModalOpen(false);
      setChoreToModify(null);
    } catch (err: any) {
      const apiError = err.response?.data?.detail || 'Failed to deactivate chore.';
      setError(apiError);
      notifications.show({
        title: 'Error',
        message: apiError,
        color: 'red',
        icon: <IconAlertCircle />,
      });
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };


  if (isLoading && chores.length === 0) {
    return (
      <Container size="md" py="xl" style={{ display: 'flex', justifyContent: 'center' }}>
        <Loader />
      </Container>
    );
  }

  const activeChores = chores.filter(c => c.is_active);
  const inactiveChores = chores.filter(c => !c.is_active);


  const rows = (choreList: Chore[]) => choreList.map((chore) => (
    <Table.Tr key={chore.id}>
      <Table.Td>
        <Text fw={500}>{chore.name}</Text>
        {chore.description && <Text fz="xs" c="dimmed">{chore.description}</Text>}
      </Table.Td>
      <Table.Td ta="right">{chore.points_value}</Table.Td>
      <Table.Td>
        <Badge color={chore.is_active ? 'green' : 'gray'} variant="light">
          {chore.is_active ? 'Active' : 'Inactive'}
        </Badge>
      </Table.Td>
      <Table.Td>{new Date(chore.created_at).toLocaleDateString()}</Table.Td>
      <Table.Td>
        <Menu shadow="md" width={200}>
          <Menu.Target>
            <ActionIcon variant="subtle">
              <IconDotsVertical size={16} />
            </ActionIcon>
          </Menu.Target>
          <Menu.Dropdown>
            <Menu.Item leftSection={<IconPencil size={14} />} onClick={() => handleOpenModal(chore)}>
              Edit
            </Menu.Item>
            {chore.is_active && (
              <Menu.Item
                leftSection={<IconCircleOff size={14} />}
                color="orange"
                onClick={() => openDeactivateConfirmModal(chore)}
              >
                Deactivate
              </Menu.Item>
            )}
            {/* Consider if reactivating inactive chores is needed here */}
            <Menu.Item
              leftSection={<IconTrash size={14} />}
              color="red"
              onClick={() => openDeleteConfirmModal(chore)}
            >
              Delete
            </Menu.Item>
          </Menu.Dropdown>
        </Menu>
      </Table.Td>
    </Table.Tr>
  ));

  return (
    <Container size="lg" py="xl">
      <Stack gap="lg">
        <Group justify="space-between">
          <Title order={2}>Manage Chores</Title>
          <Button leftSection={<IconPlus size={18} />} onClick={() => handleOpenModal()}>
            Add New Chore
          </Button>
        </Group>

        {error && !modalOpened && ( // Page level error
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" withCloseButton onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
         {successMessage && !modalOpened && ( // Page level success
          <Alert icon={<IconCircleCheck size="1rem" />} title="Success" color="green" withCloseButton onClose={() => setSuccessMessage(null)}>
            {successMessage}
          </Alert>
        )}


        {chores.length === 0 && !isLoading && (
          <Paper p="lg" shadow="xs" withBorder>
            <Text ta="center">No chores created yet. Click "Add New Chore" to get started.</Text>
          </Paper>
        )}

        {activeChores.length > 0 && (
          <>
          <Title order={4} c="dimmed">Active Chores</Title>
          <Paper shadow="md" radius="md" withBorder>
            <ScrollArea>
              <Table striped highlightOnHover withTableBorder withColumnBorders verticalSpacing="sm" horizontalSpacing="md" miw={700}>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Chore Details</Table.Th>
                    <Table.Th ta="right">Points</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th>Created</Table.Th>
                    <Table.Th>Actions</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>{rows(activeChores)}</Table.Tbody>
              </Table>
            </ScrollArea>
          </Paper>
          </>
        )}
        
        {inactiveChores.length > 0 && (
           <>
           <Title order={4} c="dimmed" mt="xl">Inactive Chores</Title>
           <Paper shadow="md" radius="md" withBorder>
             <ScrollArea>
               <Table striped highlightOnHover withTableBorder withColumnBorders verticalSpacing="sm" horizontalSpacing="md" miw={700}>
                 <Table.Thead>
                   <Table.Tr>
                     <Table.Th>Chore Details</Table.Th>
                     <Table.Th ta="right">Points</Table.Th>
                     <Table.Th>Status</Table.Th>
                     <Table.Th>Created</Table.Th>
                     <Table.Th>Actions</Table.Th> {/* Consider if different actions for inactive */}
                   </Table.Tr>
                 </Table.Thead>
                 <Table.Tbody>{rows(inactiveChores)}</Table.Tbody>
               </Table>
             </ScrollArea>
           </Paper>
           </>
        )}
      </Stack>

      <Modal
        opened={modalOpened}
        onClose={handleCloseModal}
        title={editingChore ? 'Edit Chore' : 'Add New Chore'}
        centered
        size="md"
      >
        <form onSubmit={form.onSubmit(handleSubmitChore)}>
          <Stack>
            {error && modalOpened && ( // Modal specific error
              <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" withCloseButton onClose={() => setError(null)}>
                {error}
              </Alert>
            )}
            <TextInput
              required
              label="Chore Name"
              placeholder="e.g., Clean your room"
              {...form.getInputProps('name')}
            />
            <Textarea
              label="Description (Optional)"
              placeholder="Detailed instructions for the chore"
              {...form.getInputProps('description')}
              minRows={2}
            />
            <NumberInput
              required
              label="Points Value"
              placeholder="e.g., 50"
              min={1}
              {...form.getInputProps('points_value')}
            />
            <Group justify="flex-end" mt="md">
              <Button variant="default" onClick={handleCloseModal} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button type="submit" loading={isSubmitting}>
                {editingChore ? 'Update Chore' : 'Create Chore'}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* Confirmation Modals */}
      <Modal
        opened={confirmDeleteModalOpen}
        onClose={() => setConfirmDeleteModalOpen(false)}
        title="Confirm Deletion"
        centered
        size="sm"
      >
        <Text>Are you sure you want to delete the chore "{choreToModify?.name}"? This action cannot be undone.</Text>
        <Group justify="flex-end" mt="lg">
          <Button variant="default" onClick={() => setConfirmDeleteModalOpen(false)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button color="red" onClick={handleDeleteChore} loading={isSubmitting}>
            Delete Chore
          </Button>
        </Group>
      </Modal>

      <Modal
        opened={confirmDeactivateModalOpen}
        onClose={() => setConfirmDeactivateModalOpen(false)}
        title="Confirm Deactivation"
        centered
        size="sm"
      >
        <Text>Are you sure you want to deactivate the chore "{choreToModify?.name}"? It will no longer be available for kids to complete.</Text>
        <Group justify="flex-end" mt="lg">
          <Button variant="default" onClick={() => setConfirmDeactivateModalOpen(false)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button color="orange" onClick={handleDeactivateChore} loading={isSubmitting}>
            Deactivate Chore
          </Button>
        </Group>
      </Modal>

    </Container>
  );
};

export default ManageChoresPage;
import React, { useState, useEffect } from 'react';
import * as api from '../services/api';
import { PetWithAge, PetCareSchedule, PetCareScheduleCreate, CareFrequency, User, RecommendedCareSchedule } from '../services/api';
import {
  Button,
  Modal,
  TextInput,
  Textarea,
  NumberInput,
  Select,
  MultiSelect,
  Table,
  Paper,
  Title,
  Container,
  Stack,
  Group,
  Text,
  Alert,
  Loader,
  Badge,
  ScrollArea,
  ActionIcon,
  Menu,
  Card,
} from '@mantine/core';
import { TimeInput } from '@mantine/dates';
import { useForm } from '@mantine/form';
import { IconPlus, IconAlertCircle, IconCircleCheck, IconCalendar, IconCircleOff, IconPlayerPlay, IconDotsVertical, IconSparkles, IconCheck, IconClock } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';

const DAYS_OF_WEEK = [
  { value: '0', label: 'Monday' },
  { value: '1', label: 'Tuesday' },
  { value: '2', label: 'Wednesday' },
  { value: '3', label: 'Thursday' },
  { value: '4', label: 'Friday' },
  { value: '5', label: 'Saturday' },
  { value: '6', label: 'Sunday' },
];

const formatTimeForDisplay = (time: string | undefined): string => {
  if (!time) return '';
  const [hours, minutes] = time.split(':').map(Number);
  const ampm = hours >= 12 ? 'PM' : 'AM';
  const displayHours = hours % 12 || 12;
  return `${displayHours}:${minutes.toString().padStart(2, '0')} ${ampm}`;
};

const ManageSchedulesPage: React.FC = () => {
  const [pets, setPets] = useState<PetWithAge[]>([]);
  const [schedules, setSchedules] = useState<PetCareSchedule[]>([]);
  const [kids, setKids] = useState<User[]>([]);
  const [selectedPetId, setSelectedPetId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recommendedSchedules, setRecommendedSchedules] = useState<RecommendedCareSchedule[]>([]);
  const [showRecommended, setShowRecommended] = useState(false);

  const [modalOpened, setModalOpened] = useState(false);
  const [confirmDeactivateModalOpen, setConfirmDeactivateModalOpen] = useState(false);
  const [scheduleToDeactivate, setScheduleToDeactivate] = useState<PetCareSchedule | null>(null);

  const form = useForm<PetCareScheduleCreate>({
    initialValues: {
      pet_id: '',
      task_name: '',
      description: '',
      frequency: 'daily' as CareFrequency,
      points_value: 10,
      day_of_week: undefined,
      due_by_time: undefined,
      assigned_kid_ids: [],
    },
    validate: {
      pet_id: (value: string) => (value ? null : 'Please select a pet'),
      task_name: (value: string) => (value.trim().length > 0 ? null : 'Task name is required'),
      points_value: (value: number) => (value > 0 ? null : 'Points must be greater than 0'),
      assigned_kid_ids: (value: string[]) => (value.length > 0 ? null : 'At least one kid must be assigned'),
    },
  });

  const fetchPets = async () => {
    try {
      const response = await api.getPets();
      setPets(response.data.filter(p => p.is_active));
    } catch (err) {
      console.error('Failed to fetch pets:', err);
    }
  };

  const fetchKids = async () => {
    try {
      const response = await api.getLeaderboard();
      const kidUsers = response.data.filter(u => u.role === 'kid');
      setKids(kidUsers);
    } catch (err) {
      console.error('Failed to fetch kids:', err);
    }
  };

  const fetchSchedules = async (petId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.getPetSchedules(petId);
      setSchedules(response.data);
    } catch (err) {
      setError('Failed to fetch schedules.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchRecommendedSchedules = async (petId: string) => {
    try {
      const response = await api.getRecommendedSchedules(petId);
      setRecommendedSchedules(response.data);
    } catch (err) {
      console.error('Failed to fetch recommended schedules:', err);
      setRecommendedSchedules([]);
    }
  };

  useEffect(() => {
    fetchPets();
    fetchKids();
  }, []);

  useEffect(() => {
    if (selectedPetId) {
      fetchSchedules(selectedPetId);
      fetchRecommendedSchedules(selectedPetId);
    } else {
      setSchedules([]);
      setRecommendedSchedules([]);
      setShowRecommended(false);
    }
  }, [selectedPetId]);

  const handleOpenModal = () => {
    form.reset();
    if (selectedPetId) {
      form.setFieldValue('pet_id', selectedPetId);
    }
    setModalOpened(true);
    setError(null);
  };

  const handleCloseModal = () => {
    setModalOpened(false);
    form.reset();
  };

  const handleUseRecommended = (recommended: RecommendedCareSchedule) => {
    form.reset();
    if (selectedPetId) {
      form.setValues({
        pet_id: selectedPetId,
        task_name: recommended.task_name,
        description: recommended.description,
        frequency: recommended.frequency,
        points_value: recommended.points_value,
        day_of_week: undefined,
        assigned_kid_ids: [],
      });
    }
    setModalOpened(true);
    setError(null);
  };

  const handleSubmitSchedule = async (values: PetCareScheduleCreate) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const payload = {
        ...values,
        day_of_week: values.frequency === 'weekly' && values.day_of_week !== undefined ? values.day_of_week : undefined,
      };
      await api.createPetCareSchedule(payload);
      notifications.show({
        title: 'Success',
        message: 'Schedule created successfully!',
        color: 'green',
        icon: <IconCircleCheck />,
      });
      if (selectedPetId) {
        fetchSchedules(selectedPetId);
      }
      handleCloseModal();
    } catch (err: any) {
      const apiError = err.response?.data?.detail || 'Failed to create schedule.';
      setError(apiError);
      notifications.show({
        title: 'Error',
        message: apiError,
        color: 'red',
        icon: <IconAlertCircle />,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGenerateTasks = async (scheduleId: string) => {
    setIsSubmitting(true);
    try {
      const response = await api.generatePetCareTasks(scheduleId, 7);
      notifications.show({
        title: 'Success',
        message: `Generated ${response.data.length} tasks for the next 7 days!`,
        color: 'green',
        icon: <IconCircleCheck />,
      });
    } catch (err: any) {
      const apiError = err.response?.data?.detail || 'Failed to generate tasks.';
      notifications.show({
        title: 'Error',
        message: apiError,
        color: 'red',
        icon: <IconAlertCircle />,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const openDeactivateConfirmModal = (schedule: PetCareSchedule) => {
    setScheduleToDeactivate(schedule);
    setConfirmDeactivateModalOpen(true);
  };

  const handleDeactivateSchedule = async () => {
    if (!scheduleToDeactivate) return;
    setIsSubmitting(true);
    try {
      await api.deactivatePetCareSchedule(scheduleToDeactivate.id);
      notifications.show({
        title: 'Success',
        message: 'Schedule deactivated!',
        color: 'green',
        icon: <IconCircleCheck />,
      });
      if (selectedPetId) {
        fetchSchedules(selectedPetId);
      }
      setConfirmDeactivateModalOpen(false);
      setScheduleToDeactivate(null);
    } catch (err: any) {
      const apiError = err.response?.data?.detail || 'Failed to deactivate schedule.';
      notifications.show({
        title: 'Error',
        message: apiError,
        color: 'red',
        icon: <IconAlertCircle />,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeSchedules = schedules.filter(s => s.is_active);
  const inactiveSchedules = schedules.filter(s => !s.is_active);

  return (
    <Container size="lg" py="xl">
      <Stack gap="lg">
        <Group justify="space-between">
          <Title order={2}>
            <IconCalendar size={28} style={{ marginRight: 8, verticalAlign: 'middle' }} />
            Pet Care Schedules
          </Title>
          <Button leftSection={<IconPlus size={18} />} onClick={handleOpenModal} disabled={pets.length === 0}>
            Add New Schedule
          </Button>
        </Group>

        {error && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" withCloseButton onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Select
          label="Select Pet"
          placeholder="Choose a pet to manage schedules"
          data={pets.map(p => ({ value: p.id, label: p.name }))}
          value={selectedPetId}
          onChange={setSelectedPetId}
          clearable
        />

        {!selectedPetId && pets.length > 0 && (
          <Paper p="lg" shadow="xs" withBorder>
            <Text ta="center">Select a pet to view and manage its care schedules.</Text>
          </Paper>
        )}

        {pets.length === 0 && !isLoading && (
          <Paper p="lg" shadow="xs" withBorder>
            <Text ta="center">No pets found. Add a pet first to create care schedules.</Text>
          </Paper>
        )}

        {selectedPetId && recommendedSchedules.length > 0 && (
          <>
            <Group justify="space-between" align="center">
              <Title order={4} c="dimmed">
                <IconSparkles size={18} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                Recommended Schedules
              </Title>
              <Button
                variant="subtle"
                size="xs"
                onClick={() => setShowRecommended(!showRecommended)}
              >
                {showRecommended ? 'Hide' : 'Show'} Recommendations
              </Button>
            </Group>
            {showRecommended && (
              <Paper p="md" shadow="xs" withBorder bg="blue.0">
                <Stack gap="sm">
                  <Text size="sm" c="dimmed">
                    These are research-based care tasks for your pet. Click "Use This" to create a schedule with detailed instructions.
                  </Text>
                  {recommendedSchedules.map((rec, index) => {
                    const alreadyExists = schedules.some(
                      s => s.is_active && s.task_name.toLowerCase() === rec.task_name.toLowerCase()
                    );
                    return (
                      <Card key={index} padding="sm" radius="sm" withBorder>
                        <Group justify="space-between" align="flex-start">
                          <Stack gap={4}>
                            <Group gap="xs">
                              <Text fw={500}>{rec.task_name}</Text>
                              <Badge color={rec.frequency === 'daily' ? 'blue' : 'cyan'} size="sm">
                                {rec.frequency}
                              </Badge>
                              <Badge color="green" variant="light" size="sm">
                                {rec.points_value} pts
                              </Badge>
                              {alreadyExists && (
                                <Badge color="gray" size="sm" leftSection={<IconCheck size={10} />}>
                                  Already Added
                                </Badge>
                              )}
                            </Group>
                            <Text size="xs" c="dimmed" lineClamp={2}>
                              {rec.description.split('\n')[0]}
                            </Text>
                          </Stack>
                          <Button
                            size="xs"
                            variant={alreadyExists ? 'light' : 'filled'}
                            onClick={() => handleUseRecommended(rec)}
                          >
                            Use This
                          </Button>
                        </Group>
                      </Card>
                    );
                  })}
                </Stack>
              </Paper>
            )}
          </>
        )}

        {isLoading && (
          <Container py="xl" style={{ display: 'flex', justifyContent: 'center' }}>
            <Loader />
          </Container>
        )}

        {selectedPetId && !isLoading && activeSchedules.length > 0 && (
          <>
            <Title order={4} c="dimmed">Active Schedules</Title>
            <Paper shadow="md" radius="md" withBorder>
              <ScrollArea>
                <Table striped highlightOnHover withTableBorder verticalSpacing="sm">
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Task</Table.Th>
                      <Table.Th>Frequency</Table.Th>
                      <Table.Th>Due By</Table.Th>
                      <Table.Th>Points</Table.Th>
                      <Table.Th>Assigned Kids</Table.Th>
                      <Table.Th>Actions</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {activeSchedules.map((schedule) => (
                      <Table.Tr key={schedule.id}>
                        <Table.Td>
                          <Text fw={500}>{schedule.task_name}</Text>
                          {schedule.description && <Text size="xs" c="dimmed">{schedule.description}</Text>}
                        </Table.Td>
                        <Table.Td>
                          <Badge color={schedule.frequency === 'daily' ? 'blue' : 'cyan'}>
                            {schedule.frequency}
                            {schedule.frequency === 'weekly' && schedule.day_of_week !== undefined && (
                              <> ({DAYS_OF_WEEK[schedule.day_of_week]?.label})</>
                            )}
                          </Badge>
                        </Table.Td>
                        <Table.Td>
                          {schedule.due_by_time ? (
                            <Badge color="gray" variant="light" leftSection={<IconClock size={12} />}>
                              {formatTimeForDisplay(schedule.due_by_time)}
                            </Badge>
                          ) : (
                            <Text size="sm" c="dimmed">End of day</Text>
                          )}
                        </Table.Td>
                        <Table.Td>{schedule.points_value}</Table.Td>
                        <Table.Td>
                          {schedule.assigned_kid_ids.map(kidId => {
                            const kid = kids.find(k => k.username === kidId);
                            return (
                              <Badge key={kidId} variant="light" mr={4}>
                                {kid?.username || kidId}
                              </Badge>
                            );
                          })}
                        </Table.Td>
                        <Table.Td>
                          <Menu shadow="md" width={200}>
                            <Menu.Target>
                              <ActionIcon variant="subtle">
                                <IconDotsVertical size={16} />
                              </ActionIcon>
                            </Menu.Target>
                            <Menu.Dropdown>
                              <Menu.Item
                                leftSection={<IconPlayerPlay size={14} />}
                                onClick={() => handleGenerateTasks(schedule.id)}
                              >
                                Generate Tasks (7 days)
                              </Menu.Item>
                              <Menu.Item
                                leftSection={<IconCircleOff size={14} />}
                                color="orange"
                                onClick={() => openDeactivateConfirmModal(schedule)}
                              >
                                Deactivate
                              </Menu.Item>
                            </Menu.Dropdown>
                          </Menu>
                        </Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </ScrollArea>
            </Paper>
          </>
        )}

        {selectedPetId && !isLoading && schedules.length === 0 && (
          <Paper p="lg" shadow="xs" withBorder>
            <Text ta="center">No schedules for this pet. Create one to start assigning care tasks.</Text>
          </Paper>
        )}

        {selectedPetId && inactiveSchedules.length > 0 && (
          <>
            <Title order={4} c="dimmed" mt="xl">Inactive Schedules</Title>
            <Paper shadow="md" radius="md" withBorder>
              <ScrollArea>
                <Table striped highlightOnHover withTableBorder verticalSpacing="sm">
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Task</Table.Th>
                      <Table.Th>Frequency</Table.Th>
                      <Table.Th>Points</Table.Th>
                      <Table.Th>Status</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {inactiveSchedules.map((schedule) => (
                      <Table.Tr key={schedule.id}>
                        <Table.Td>{schedule.task_name}</Table.Td>
                        <Table.Td>{schedule.frequency}</Table.Td>
                        <Table.Td>{schedule.points_value}</Table.Td>
                        <Table.Td><Badge color="gray">Inactive</Badge></Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </ScrollArea>
            </Paper>
          </>
        )}
      </Stack>

      <Modal
        opened={modalOpened}
        onClose={handleCloseModal}
        title="Add New Schedule"
        centered
        size="md"
      >
        <form onSubmit={form.onSubmit(handleSubmitSchedule)}>
          <Stack>
            {error && (
              <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" withCloseButton onClose={() => setError(null)}>
                {error}
              </Alert>
            )}
            <Select
              required
              label="Pet"
              placeholder="Select a pet"
              data={pets.map(p => ({ value: p.id, label: p.name }))}
              {...form.getInputProps('pet_id')}
            />
            <TextInput
              required
              label="Task Name"
              placeholder="e.g., Feed Spike"
              {...form.getInputProps('task_name')}
            />
            <Textarea
              label="Description (Optional)"
              placeholder="Instructions for the task"
              {...form.getInputProps('description')}
              minRows={2}
            />
            <Select
              required
              label="Frequency"
              data={[
                { value: 'daily', label: 'Daily' },
                { value: 'weekly', label: 'Weekly' },
              ]}
              {...form.getInputProps('frequency')}
            />
            {form.values.frequency === 'weekly' && (
              <Select
                label="Day of Week"
                placeholder="Select day"
                data={DAYS_OF_WEEK}
                value={form.values.day_of_week?.toString()}
                onChange={(val) => form.setFieldValue('day_of_week', val ? parseInt(val) : undefined)}
              />
            )}
            <TimeInput
              label="Due By Time (Optional)"
              description="When should this task be completed by?"
              placeholder="e.g., 10:00 AM"
              leftSection={<IconClock size={16} />}
              value={form.values.due_by_time || ''}
              onChange={(e) => form.setFieldValue('due_by_time', e.currentTarget.value || undefined)}
            />
            <NumberInput
              required
              label="Points Value"
              placeholder="e.g., 10"
              min={1}
              {...form.getInputProps('points_value')}
            />
            <MultiSelect
              required
              label="Assign to Kids"
              placeholder="Select kids for rotation"
              data={kids.map(k => ({ value: k.username, label: k.username }))}
              {...form.getInputProps('assigned_kid_ids')}
            />
            <Group justify="flex-end" mt="md">
              <Button variant="default" onClick={handleCloseModal} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button type="submit" loading={isSubmitting}>
                Create Schedule
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      <Modal
        opened={confirmDeactivateModalOpen}
        onClose={() => setConfirmDeactivateModalOpen(false)}
        title="Confirm Deactivation"
        centered
        size="sm"
      >
        <Text>Are you sure you want to deactivate the schedule "{scheduleToDeactivate?.task_name}"?</Text>
        <Group justify="flex-end" mt="lg">
          <Button variant="default" onClick={() => setConfirmDeactivateModalOpen(false)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button color="orange" onClick={handleDeactivateSchedule} loading={isSubmitting}>
            Deactivate
          </Button>
        </Group>
      </Modal>
    </Container>
  );
};

export default ManageSchedulesPage;

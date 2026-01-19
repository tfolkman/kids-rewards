import React, { useState, useEffect } from 'react';
import * as api from '../services/api';
import { PetCareTask, PetCareTaskSubmission } from '../services/api';
import {
  Container,
  Title,
  Paper,
  Stack,
  Group,
  Text,
  Alert,
  Loader,
  Badge,
  Card,
  Button,
  Modal,
  Textarea,
  Spoiler,
  Box,
} from '@mantine/core';
import { IconPaw, IconAlertCircle, IconCircleCheck, IconClock, IconSend, IconBook } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';

const STATUS_COLORS: Record<string, string> = {
  assigned: 'blue',
  pending_approval: 'yellow',
  approved: 'green',
  rejected: 'red',
  skipped: 'gray',
};

type UrgencyLevel = 'overdue' | 'due_soon' | 'normal';

interface TaskUrgency {
  level: UrgencyLevel;
  hoursLate?: number;
  hoursUntilDue?: number;
}

const getTaskUrgency = (dueDate: string): TaskUrgency => {
  const now = new Date();
  const due = new Date(dueDate);
  const diffMs = due.getTime() - now.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);

  if (diffHours < 0) {
    return { level: 'overdue', hoursLate: Math.abs(Math.floor(diffHours)) };
  } else if (diffHours <= 1) {
    return { level: 'due_soon', hoursUntilDue: Math.ceil(diffHours * 60) };
  }
  return { level: 'normal' };
};

const formatDueDateTime = (dueDate: string): string => {
  const date = new Date(dueDate);
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(tomorrow.getDate() + 1);

  const dateOptions: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
  const timeOptions: Intl.DateTimeFormatOptions = { hour: 'numeric', minute: '2-digit', hour12: true };

  const isToday = date.toDateString() === today.toDateString();
  const isTomorrow = date.toDateString() === tomorrow.toDateString();

  let dateStr = '';
  if (isToday) {
    dateStr = 'Today';
  } else if (isTomorrow) {
    dateStr = 'Tomorrow';
  } else {
    dateStr = date.toLocaleDateString(undefined, dateOptions);
  }

  const timeStr = date.toLocaleTimeString(undefined, timeOptions);
  return `${dateStr} at ${timeStr}`;
};

const getUrgencyBorderStyle = (urgency: TaskUrgency): React.CSSProperties => {
  if (urgency.level === 'overdue') {
    return { borderLeft: '4px solid var(--mantine-color-red-6)' };
  } else if (urgency.level === 'due_soon') {
    return { borderLeft: '4px solid var(--mantine-color-yellow-6)' };
  }
  return {};
};

const MyPetTasksPage: React.FC = () => {
  const [tasks, setTasks] = useState<PetCareTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [submitModalOpened, setSubmitModalOpened] = useState(false);
  const [selectedTask, setSelectedTask] = useState<PetCareTask | null>(null);
  const [submissionNotes, setSubmissionNotes] = useState('');

  const fetchTasks = async () => {
    try {
      const response = await api.getMyPetTasks();
      // Sort: overdue first, then by due date (earliest first)
      setTasks(response.data.sort((a, b) => {
        const urgencyA = getTaskUrgency(a.due_date);
        const urgencyB = getTaskUrgency(b.due_date);
        // Overdue tasks should come first
        if (urgencyA.level === 'overdue' && urgencyB.level !== 'overdue') return -1;
        if (urgencyB.level === 'overdue' && urgencyA.level !== 'overdue') return 1;
        // Then sort by due date
        return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
      }));
    } catch (err) {
      setError('Failed to fetch pet tasks.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const openSubmitModal = (task: PetCareTask) => {
    setSelectedTask(task);
    setSubmissionNotes('');
    setSubmitModalOpened(true);
  };

  const handleSubmitTask = async () => {
    if (!selectedTask) return;
    setIsSubmitting(true);
    try {
      const data: PetCareTaskSubmission = {};
      if (submissionNotes.trim()) {
        data.notes = submissionNotes;
      }
      await api.submitPetCareTask(selectedTask.id, data);
      notifications.show({
        title: 'Success',
        message: 'Task submitted for approval!',
        color: 'green',
        icon: <IconCircleCheck />,
      });
      fetchTasks();
      setSubmitModalOpened(false);
      setSelectedTask(null);
    } catch (err: any) {
      const apiError = err.response?.data?.detail || 'Failed to submit task.';
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

  if (isLoading) {
    return (
      <Container size="md" py="xl" style={{ display: 'flex', justifyContent: 'center' }}>
        <Loader />
      </Container>
    );
  }

  const assignedTasks = tasks.filter(t => t.status === 'assigned');
  const pendingTasks = tasks.filter(t => t.status === 'pending_approval');
  const completedTasks = tasks.filter(t => t.status === 'approved' || t.status === 'rejected');

  return (
    <Container size="lg" py="xl">
      <Stack gap="lg">
        <Title order={2}>
          <IconPaw size={28} style={{ marginRight: 8, verticalAlign: 'middle' }} />
          My Pet Tasks
        </Title>

        {error && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" withCloseButton onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {tasks.length === 0 && !isLoading && (
          <Paper p="lg" shadow="xs" withBorder>
            <Text ta="center">No pet care tasks assigned to you yet.</Text>
          </Paper>
        )}

        {assignedTasks.length > 0 && (
          <>
            <Title order={4} c="dimmed">To Do</Title>
            <Stack gap="sm">
              {assignedTasks.map((task) => {
                const urgency = getTaskUrgency(task.due_date);
                return (
                  <Card
                    key={task.id}
                    shadow="sm"
                    padding="md"
                    radius="md"
                    withBorder
                    style={getUrgencyBorderStyle(urgency)}
                  >
                    <Stack gap="sm">
                      <Group justify="space-between" align="flex-start">
                        <Stack gap="xs">
                          <Group gap="xs">
                            <Text fw={600}>{task.task_name}</Text>
                            <Badge color="cyan">{task.pet_name}</Badge>
                            {urgency.level === 'overdue' && (
                              <Badge color="red">
                                {urgency.hoursLate === 0 ? 'Just overdue' :
                                  urgency.hoursLate === 1 ? '1 hour late' :
                                  `${urgency.hoursLate} hours late`}
                              </Badge>
                            )}
                            {urgency.level === 'due_soon' && (
                              <Badge color="yellow">Due soon!</Badge>
                            )}
                          </Group>
                          <Group gap="xs">
                            <IconClock size={14} />
                            <Text
                              size="sm"
                              c={urgency.level === 'overdue' ? 'red' : urgency.level === 'due_soon' ? 'yellow.7' : 'dimmed'}
                              fw={urgency.level !== 'normal' ? 500 : undefined}
                            >
                              Due: {formatDueDateTime(task.due_date)}
                            </Text>
                            <Badge color="blue" variant="light">{task.points_value} pts</Badge>
                          </Group>
                        </Stack>
                        <Button
                          leftSection={<IconSend size={16} />}
                          onClick={() => openSubmitModal(task)}
                          color={urgency.level === 'overdue' ? 'red' : undefined}
                        >
                          Complete
                        </Button>
                      </Group>
                      {task.description && (
                        <Spoiler
                          maxHeight={0}
                          showLabel={<Group gap={4}><IconBook size={14} /> Show Instructions</Group>}
                          hideLabel="Hide Instructions"
                          styles={{
                            control: { color: 'var(--mantine-color-blue-6)', fontWeight: 500 }
                          }}
                        >
                          <Box
                            p="sm"
                            bg="gray.0"
                            style={{ borderRadius: 8, whiteSpace: 'pre-wrap', fontFamily: 'inherit' }}
                          >
                            <Text size="sm" style={{ lineHeight: 1.6 }}>{task.description}</Text>
                          </Box>
                        </Spoiler>
                      )}
                    </Stack>
                  </Card>
                );
              })}
            </Stack>
          </>
        )}

        {pendingTasks.length > 0 && (
          <>
            <Title order={4} c="dimmed" mt="xl">Awaiting Approval</Title>
            <Stack gap="sm">
              {pendingTasks.map((task) => (
                <Card key={task.id} shadow="sm" padding="md" radius="md" withBorder>
                  <Group justify="space-between">
                    <Stack gap="xs">
                      <Group gap="xs">
                        <Text fw={600}>{task.task_name}</Text>
                        <Badge color="cyan">{task.pet_name}</Badge>
                        <Badge color="yellow">Pending Approval</Badge>
                      </Group>
                      <Text size="sm" c="dimmed">
                        Submitted: {task.submitted_at ? new Date(task.submitted_at).toLocaleDateString() : 'N/A'}
                      </Text>
                      {task.submission_notes && (
                        <Text size="sm" c="dimmed">Notes: {task.submission_notes}</Text>
                      )}
                    </Stack>
                    <Badge color="blue" variant="light" size="lg">{task.points_value} pts</Badge>
                  </Group>
                </Card>
              ))}
            </Stack>
          </>
        )}

        {completedTasks.length > 0 && (
          <>
            <Title order={4} c="dimmed" mt="xl">History</Title>
            <Stack gap="sm">
              {completedTasks.slice(0, 10).map((task) => (
                <Card key={task.id} shadow="sm" padding="md" radius="md" withBorder>
                  <Group justify="space-between">
                    <Stack gap="xs">
                      <Group gap="xs">
                        <Text fw={600}>{task.task_name}</Text>
                        <Badge color="cyan">{task.pet_name}</Badge>
                        <Badge color={STATUS_COLORS[task.status]}>
                          {task.status.replace('_', ' ')}
                        </Badge>
                      </Group>
                      <Text size="sm" c="dimmed">
                        Reviewed: {task.reviewed_at ? new Date(task.reviewed_at).toLocaleDateString() : 'N/A'}
                      </Text>
                    </Stack>
                    <Badge
                      color={task.status === 'approved' ? 'green' : 'red'}
                      variant="light"
                      size="lg"
                    >
                      {task.status === 'approved' ? `+${task.points_value} pts` : '0 pts'}
                    </Badge>
                  </Group>
                </Card>
              ))}
            </Stack>
          </>
        )}
      </Stack>

      <Modal
        opened={submitModalOpened}
        onClose={() => setSubmitModalOpened(false)}
        title={`Submit: ${selectedTask?.task_name}`}
        centered
        size="lg"
      >
        <Stack>
          <Text size="sm" c="dimmed">
            Mark this task as complete for {selectedTask?.pet_name}.
          </Text>
          {selectedTask?.description && (
            <Box
              p="sm"
              bg="gray.0"
              style={{ borderRadius: 8, whiteSpace: 'pre-wrap', fontFamily: 'inherit', maxHeight: 300, overflowY: 'auto' }}
            >
              <Text size="sm" style={{ lineHeight: 1.6 }}>{selectedTask.description}</Text>
            </Box>
          )}
          <Textarea
            label="Notes (Optional)"
            placeholder="Any notes about completing this task"
            value={submissionNotes}
            onChange={(e) => setSubmissionNotes(e.currentTarget.value)}
            minRows={3}
          />
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={() => setSubmitModalOpened(false)} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button onClick={handleSubmitTask} loading={isSubmitting}>
              Submit for Approval
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
};

export default MyPetTasksPage;

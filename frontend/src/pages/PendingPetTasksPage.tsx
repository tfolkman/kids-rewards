import React, { useState, useEffect } from 'react';
import * as api from '../services/api';
import { PetCareTask } from '../services/api';
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
  ActionIcon,
} from '@mantine/core';
import { IconPaw, IconAlertCircle, IconCircleCheck, IconCheck, IconX } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';

const PendingPetTasksPage: React.FC = () => {
  const [tasks, setTasks] = useState<PetCareTask[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = async () => {
    try {
      const response = await api.getPendingPetTaskSubmissions();
      setTasks(response.data.sort((a, b) =>
        new Date(a.submitted_at || a.created_at).getTime() - new Date(b.submitted_at || b.created_at).getTime()
      ));
    } catch (err) {
      setError('Failed to fetch pending pet tasks.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleApprove = async (taskId: string) => {
    setIsSubmitting(taskId);
    try {
      await api.approvePetCareTask({ task_id: taskId });
      notifications.show({
        title: 'Approved',
        message: 'Task approved and points awarded!',
        color: 'green',
        icon: <IconCircleCheck />,
      });
      fetchTasks();
    } catch (err: any) {
      const apiError = err.response?.data?.detail || 'Failed to approve task.';
      notifications.show({
        title: 'Error',
        message: apiError,
        color: 'red',
        icon: <IconAlertCircle />,
      });
    } finally {
      setIsSubmitting(null);
    }
  };

  const handleReject = async (taskId: string) => {
    setIsSubmitting(taskId);
    try {
      await api.rejectPetCareTask({ task_id: taskId });
      notifications.show({
        title: 'Rejected',
        message: 'Task rejected.',
        color: 'orange',
        icon: <IconX />,
      });
      fetchTasks();
    } catch (err: any) {
      const apiError = err.response?.data?.detail || 'Failed to reject task.';
      notifications.show({
        title: 'Error',
        message: apiError,
        color: 'red',
        icon: <IconAlertCircle />,
      });
    } finally {
      setIsSubmitting(null);
    }
  };

  if (isLoading) {
    return (
      <Container size="md" py="xl" style={{ display: 'flex', justifyContent: 'center' }}>
        <Loader />
      </Container>
    );
  }

  return (
    <Container size="lg" py="xl">
      <Stack gap="lg">
        <Title order={2}>
          <IconPaw size={28} style={{ marginRight: 8, verticalAlign: 'middle' }} />
          Pending Pet Task Approvals
        </Title>

        {error && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" withCloseButton onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {tasks.length === 0 && !isLoading && (
          <Paper p="lg" shadow="xs" withBorder>
            <Text ta="center">No pending pet task submissions to review.</Text>
          </Paper>
        )}

        {tasks.length > 0 && (
          <Stack gap="md">
            {tasks.map((task) => (
              <Card key={task.id} shadow="sm" padding="md" radius="md" withBorder>
                <Group justify="space-between" align="flex-start">
                  <Stack gap="xs" style={{ flex: 1 }}>
                    <Group gap="xs">
                      <Text fw={600}>{task.task_name}</Text>
                      <Badge color="cyan">{task.pet_name}</Badge>
                      <Badge color="yellow">Pending Approval</Badge>
                    </Group>
                    {task.description && (
                      <Text size="sm" c="dimmed">{task.description}</Text>
                    )}
                    <Group gap="md">
                      <Text size="sm">
                        <Text span fw={500}>Submitted by:</Text> {task.assigned_to_kid_username}
                      </Text>
                      <Text size="sm">
                        <Text span fw={500}>Due:</Text> {new Date(task.due_date).toLocaleDateString()}
                      </Text>
                      <Text size="sm">
                        <Text span fw={500}>Submitted:</Text> {task.submitted_at ? new Date(task.submitted_at).toLocaleString() : 'N/A'}
                      </Text>
                    </Group>
                    {task.submission_notes && (
                      <Paper p="xs" withBorder>
                        <Text size="sm" c="dimmed" fs="italic">
                          Notes: "{task.submission_notes}"
                        </Text>
                      </Paper>
                    )}
                  </Stack>

                  <Stack gap="xs" align="center">
                    <Badge color="blue" variant="light" size="lg">
                      {task.points_value} pts
                    </Badge>
                    <Group gap="xs">
                      <Button
                        color="green"
                        size="sm"
                        leftSection={<IconCheck size={16} />}
                        onClick={() => handleApprove(task.id)}
                        loading={isSubmitting === task.id}
                        disabled={isSubmitting !== null && isSubmitting !== task.id}
                      >
                        Approve
                      </Button>
                      <Button
                        color="red"
                        variant="light"
                        size="sm"
                        leftSection={<IconX size={16} />}
                        onClick={() => handleReject(task.id)}
                        loading={isSubmitting === task.id}
                        disabled={isSubmitting !== null && isSubmitting !== task.id}
                      >
                        Reject
                      </Button>
                    </Group>
                  </Stack>
                </Group>
              </Card>
            ))}
          </Stack>
        )}
      </Stack>
    </Container>
  );
};

export default PendingPetTasksPage;

import React, { useState, useEffect } from 'react';
import {
  Container,
  Title,
  Table,
  Text,
  Paper,
  Loader,
  Alert,
  Stack,
  Badge,
  Button,
  Group,
  Modal,
  Textarea,
  ScrollArea,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconAlertCircle, IconCircleCheck, IconCalendar, IconClipboardCheck } from '@tabler/icons-react';
import { getMyAssignedChores, submitAssignmentCompletion } from '../services/api';
import type { ChoreAssignment, ChoreAssignmentSubmission } from '../services/api';
import { useAuth } from '../App';

const MyAssignedChoresPage: React.FC = () => {
  const [assignments, setAssignments] = useState<ChoreAssignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submissionModalOpen, setSubmissionModalOpen] = useState(false);
  const [selectedAssignment, setSelectedAssignment] = useState<ChoreAssignment | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { currentUser } = useAuth();

  const form = useForm<ChoreAssignmentSubmission>({
    initialValues: {
      submission_notes: '',
    },
  });

  const fetchAssignments = async () => {
    if (!currentUser || currentUser.role !== 'kid') {
      setError('You must be logged in as a kid to view assigned chores.');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await getMyAssignedChores();
      // Sort by assigned_at date, newest first
      const sortedAssignments = response.data.sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      console.log('Sorted assignments:', sortedAssignments);
      setAssignments(sortedAssignments);
    } catch (err: any) {
      setError('Failed to fetch assigned chores. Please try again.');
      console.error('Error fetching assignments:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAssignments();
  }, [currentUser]);

  const getStatusBadge = (status: string) => {
    let color = 'gray';
    switch (status) {
      case 'assigned':
        color = 'blue';
        break;
      case 'submitted':
        color = 'yellow';
        break;
      case 'approved':
        color = 'green';
        break;
      case 'rejected':
        color = 'red';
        break;
    }
    
    // Display user-friendly labels
    const displayText = status === 'assigned' ? 'Pending' : status.charAt(0).toUpperCase() + status.slice(1);
    
    return (
      <Badge color={color} variant="light">
        {displayText}
      </Badge>
    );
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const openSubmissionModal = (assignment: ChoreAssignment) => {
    setSelectedAssignment(assignment);
    form.reset();
    setSubmissionModalOpen(true);
  };

  const handleSubmitCompletion = async (values: ChoreAssignmentSubmission) => {
    if (!selectedAssignment) return;

    setIsSubmitting(true);
    try {
      await submitAssignmentCompletion(selectedAssignment.id, values);
      notifications.show({
        title: 'Assignment Submitted!',
        message: 'Your completed assignment has been submitted for review.',
        color: 'green',
        icon: <IconCircleCheck />,
      });
      setSubmissionModalOpen(false);
      setSelectedAssignment(null);
      fetchAssignments(); // Refresh the list
    } catch (err: any) {
      let errorMessage = 'Failed to submit assignment.';
      
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          // Handle FastAPI validation errors which return an array
          errorMessage = err.response.data.detail.map((e: any) => e.msg || e.message || 'Validation error').join(', ');
        } else {
          errorMessage = 'An error occurred during submission.';
        }
      }
      
      notifications.show({
        title: 'Submission Failed',
        message: errorMessage,
        color: 'red',
        icon: <IconAlertCircle />,
      });
      console.error('Error submitting assignment:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const isDueSoon = (dueDate: string | undefined) => {
    if (!dueDate) return false;
    const due = new Date(dueDate);
    const today = new Date();
    const diffDays = Math.ceil((due.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
    return diffDays <= 2 && diffDays >= 0;
  };

  const isOverdue = (dueDate: string | undefined) => {
    if (!dueDate) return false;
    const due = new Date(dueDate);
    const today = new Date();
    return due < today;
  };

  if (currentUser?.role !== 'kid') {
    return (
      <Container size="md" my="xl">
        <Alert icon={<IconAlertCircle size="1rem" />} title="Access Denied" color="red" radius="md">
          You must be logged in as a kid to view assigned chores.
        </Alert>
      </Container>
    );
  }

  if (isLoading) {
    return (
      <Container size="md" py="xl" style={{ display: 'flex', justifyContent: 'center' }}>
        <Loader />
      </Container>
    );
  }

  const pendingAssignments = assignments.filter(a => a.assignment_status === 'assigned');
  console.log('Pending assignments:', pendingAssignments);
  const submittedAssignments = assignments.filter(a => a.assignment_status === 'submitted');
  const completedAssignments = assignments.filter(a => ['approved', 'rejected'].includes(a.assignment_status));

  const renderAssignmentTable = (assignments: ChoreAssignment[], showSubmitButton = false) => (
    <Table striped highlightOnHover withTableBorder withColumnBorders verticalSpacing="sm">
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Chore</Table.Th>
          <Table.Th>Assigned By</Table.Th>
          <Table.Th ta="right">Points</Table.Th>
          <Table.Th>Due Date</Table.Th>
          <Table.Th>Status</Table.Th>
          {showSubmitButton && <Table.Th ta="center">Action</Table.Th>}
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {assignments.map((assignment) => (
          <Table.Tr key={assignment.id}>
            <Table.Td>
              <Stack gap="xs">
                <Text fw={500}>{assignment.chore_name}</Text>
                {assignment.notes && (
                  <Text size="sm" c="dimmed">
                    Note: {assignment.notes}
                  </Text>
                )}
              </Stack>
            </Table.Td>
            <Table.Td>{assignment.assigned_by_parent_id}</Table.Td>
            <Table.Td ta="right">
              <Badge color="green" variant="light">
                {assignment.points_value}
              </Badge>
            </Table.Td>
            <Table.Td>
              {assignment.due_date ? (
                <Group gap="xs">
                  <IconCalendar size={14} />
                  <Text
                    size="sm"
                    c={
                      isOverdue(assignment.due_date)
                        ? 'red'
                        : isDueSoon(assignment.due_date)
                        ? 'orange'
                        : undefined
                    }
                    fw={isOverdue(assignment.due_date) || isDueSoon(assignment.due_date) ? 500 : undefined}
                  >
                    {formatDate(assignment.due_date)}
                    {isOverdue(assignment.due_date) && ' (Overdue)'}
                    {isDueSoon(assignment.due_date) && !isOverdue(assignment.due_date) && ' (Due Soon)'}
                  </Text>
                </Group>
              ) : (
                <Text size="sm" c="dimmed">
                  No deadline
                </Text>
              )}
            </Table.Td>
            <Table.Td>{getStatusBadge(assignment.assignment_status)}</Table.Td>
            {showSubmitButton && (
              <Table.Td>
                <Button
                  size="xs"
                  variant="light"
                  color="green"
                  onClick={() => openSubmissionModal(assignment)}
                  leftSection={<IconClipboardCheck size={14} />}
                >
                  Mark Complete
                </Button>
              </Table.Td>
            )}
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  );

  return (
    <Container size="lg" py="xl">
      <Stack gap="lg">
        <Title order={2} ta="center">
          My Assigned Chores
        </Title>

        {error && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" withCloseButton onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Pending Assignments */}
        <Paper shadow="md" radius="md" withBorder>
          <Group p="md" bg="blue.0">
            <Title order={4} c="blue.7">
              To Do ({pendingAssignments.length})
            </Title>
          </Group>
          {pendingAssignments.length === 0 ? (
            <Text ta="center" py="xl" c="dimmed">
              No pending assignments. Great job!
            </Text>
          ) : (
            <ScrollArea>
              {renderAssignmentTable(pendingAssignments, true)}
            </ScrollArea>
          )}
        </Paper>

        {/* Submitted Assignments */}
        {submittedAssignments.length > 0 && (
          <Paper shadow="md" radius="md" withBorder>
            <Group p="md" bg="yellow.0">
              <Title order={4} c="yellow.7">
                Waiting for Review ({submittedAssignments.length})
              </Title>
            </Group>
            <ScrollArea>
              {renderAssignmentTable(submittedAssignments)}
            </ScrollArea>
          </Paper>
        )}

        {/* Completed Assignments */}
        {completedAssignments.length > 0 && (
          <Paper shadow="md" radius="md" withBorder>
            <Group p="md" bg="gray.0">
              <Title order={4} c="gray.7">
                Completed ({completedAssignments.length})
              </Title>
            </Group>
            <ScrollArea>
              {renderAssignmentTable(completedAssignments)}
            </ScrollArea>
          </Paper>
        )}

        {assignments.length === 0 && (
          <Paper p="lg" shadow="xs" withBorder>
            <Text ta="center" c="dimmed">
              No chores have been assigned to you yet.
            </Text>
          </Paper>
        )}
      </Stack>

      {/* Submission Modal */}
      <Modal
        opened={submissionModalOpen}
        onClose={() => setSubmissionModalOpen(false)}
        title="Mark Assignment as Complete"
        centered
        size="md"
      >
        {selectedAssignment && (
          <form onSubmit={form.onSubmit(handleSubmitCompletion)}>
            <Stack>
              <Paper withBorder p="md" bg="gray.0">
                <Text fw={500}>{selectedAssignment.chore_name}</Text>
                <Text size="sm" c="dimmed">
                  Worth {selectedAssignment.points_value} points
                </Text>
                {selectedAssignment.notes && (
                  <Text size="sm" mt="xs">
                    <strong>Instructions:</strong> {selectedAssignment.notes}
                  </Text>
                )}
              </Paper>

              <Textarea
                label="Completion Notes (Optional)"
                placeholder="Add any notes about how you completed this chore..."
                minRows={3}
                {...form.getInputProps('submission_notes')}
              />

              <Group justify="flex-end" mt="md">
                <Button variant="default" onClick={() => setSubmissionModalOpen(false)} disabled={isSubmitting}>
                  Cancel
                </Button>
                <Button type="submit" loading={isSubmitting} color="green">
                  Submit Completion
                </Button>
              </Group>
            </Stack>
          </form>
        )}
      </Modal>
    </Container>
  );
};

export default MyAssignedChoresPage;
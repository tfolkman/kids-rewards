
import React, { useState, useEffect } from 'react';
import {
  Container,
  Title,
  Paper,
  Stack,
  Group,
  Button,
  Modal,
  Select,
  Textarea,
  Alert,
  Table,
  Text,
  Badge,
  ScrollArea,
  ActionIcon,
  Menu,
  Loader,
  TextInput,
} from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconPlus, IconAlertCircle, IconCircleCheck, IconCalendar, IconDotsVertical, IconEye } from '@tabler/icons-react';
import { 
  assignChoreToKid, 
  getMyCreatedAssignments, 
  getMyCreatedChores, 
  getLeaderboard,
  getPendingAssignmentSubmissions,
  approveAssignmentSubmission,
  rejectAssignmentSubmission
} from '../services/api';
import type { ChoreAssignmentCreate, ChoreAssignment, Chore, User } from '../services/api';
import { useAuth } from '../App';

const AssignChoresPage: React.FC = () => {
  const [assignments, setAssignments] = useState<ChoreAssignment[]>([]);
  const [chores, setChores] = useState<Chore[]>([]);
  const [kids, setKids] = useState<User[]>([]);
  const [pendingSubmissions, setPendingSubmissions] = useState<ChoreAssignment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [selectedSubmission, setSelectedSubmission] = useState<ChoreAssignment | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { currentUser } = useAuth();

  const form = useForm<ChoreAssignmentCreate>({
    initialValues: {
      chore_id: '',
      assigned_to_kid_id: '',
      due_date: '',
      notes: '',
    },
    validate: {
      chore_id: (value) => (value ? null : 'Please select a chore'),
      assigned_to_kid_id: (value) => (value ? null : 'Please select a kid'),
    },
  });

  const fetchData = async () => {
    if (!currentUser || currentUser.role !== 'parent') {
      setError('You must be logged in as a parent to manage chore assignments.');
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const [assignmentsRes, choresRes, usersRes, submissionsRes] = await Promise.all([
        getMyCreatedAssignments(),
        getMyCreatedChores(),
        getLeaderboard(), // This returns all users; we'll filter for kids
        getPendingAssignmentSubmissions(),
      ]);

      const sortedAssignments = assignmentsRes.data.sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
      setAssignments(sortedAssignments);

      const activeChores = choresRes.data.filter(chore => chore.is_active);
      setChores(activeChores);

      const kidUsers = usersRes.data.filter(user => user.role === 'kid');
      setKids(kidUsers);

      setPendingSubmissions(submissionsRes.data);
    } catch (err: any) {
      setError('Failed to fetch data. Please try again.');
      console.error('Error fetching data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [currentUser]);

  const handleAssignChore = async (values: ChoreAssignmentCreate) => {
    setIsSubmitting(true);
    try {
      const payload = {
        ...values,
        due_date: values.due_date || undefined,
      };
      await assignChoreToKid(payload);
      notifications.show({
        title: 'Assignment Created!',
        message: 'Chore has been assigned successfully.',
        color: 'green',
        icon: <IconCircleCheck />,
      });
      setAssignModalOpen(false);
      form.reset();
      fetchData(); // Refresh the data
    } catch (err: any) {
      let errorMessage = 'Failed to assign chore.';
      
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          errorMessage = err.response.data.detail.map((e: any) => e.msg || e.message || 'Validation error').join(', ');
        }
      }
      
      notifications.show({
        title: 'Assignment Failed',
        message: errorMessage,
        color: 'red',
        icon: <IconAlertCircle />,
      });
      console.error('Error assigning chore:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSubmissionAction = async (assignmentId: string, action: 'approve' | 'reject') => {
    setIsSubmitting(true);
    try {
      if (action === 'approve') {
        await approveAssignmentSubmission({ assignment_id: assignmentId });
      } else {
        await rejectAssignmentSubmission({ assignment_id: assignmentId });
      }
      
      notifications.show({
        title: `Assignment ${action === 'approve' ? 'Approved' : 'Rejected'}!`,
        message: `The assignment has been ${action === 'approve' ? 'approved' : 'rejected'} successfully.`,
        color: action === 'approve' ? 'green' : 'red',
        icon: <IconCircleCheck />,
      });
      
      setReviewModalOpen(false);
      setSelectedSubmission(null);
      fetchData(); // Refresh the data
    } catch (err: any) {
      let errorMessage = `Failed to ${action} assignment.`;
      
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMessage = err.response.data.detail;
        }
      }
      
      notifications.show({
        title: `${action === 'approve' ? 'Approval' : 'Rejection'} Failed`,
        message: errorMessage,
        color: 'red',
        icon: <IconAlertCircle />,
      });
      console.error(`Error ${action}ing assignment:`, err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const openReviewModal = (submission: ChoreAssignment) => {
    setSelectedSubmission(submission);
    setReviewModalOpen(true);
  };

  const getStatusBadge = (status: string) => {
    // Handle undefined, null, or empty status
    if (!status || typeof status !== 'string') {
      return (
        <Badge color="gray" variant="light">
          Unknown
        </Badge>
      );
    }

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
    const safeStatus = displayText || 'unknown';
    return (
      <Badge color={color} variant="light">
        {safeStatus}
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

  if (currentUser?.role !== 'parent') {
    return (
      <Container size="md" my="xl">
        <Alert icon={<IconAlertCircle size="1rem" />} title="Access Denied" color="red" radius="md">
          You must be logged in as a parent to assign chores.
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

  return (
    <Container size="lg" py="xl">
      <Stack gap="lg">
        <Group justify="space-between">
          <Title order={2}>Assign Chores</Title>
          <Button
            leftSection={<IconPlus size={18} />}
            onClick={() => setAssignModalOpen(true)}
            disabled={chores.length === 0 || kids.length === 0}
          >
            Assign Chore
          </Button>
        </Group>

        {error && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" withCloseButton onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {(chores.length === 0 || kids.length === 0) && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Setup Required" color="orange">
            {chores.length === 0 && kids.length === 0 
              ? 'You need to create chores and have kids registered before you can assign chores.'
              : chores.length === 0
              ? 'You need to create some chores before you can assign them.'
              : 'You need kids registered in the system before you can assign chores.'}
          </Alert>
        )}

        {/* Pending Submissions */}
        {pendingSubmissions.length > 0 && (
          <Paper shadow="md" radius="md" withBorder>
            <Group p="md" bg="yellow.0">
              <Title order={4} c="yellow.7">
                Pending Review ({pendingSubmissions.length})
              </Title>
            </Group>
            <ScrollArea>
              <Table striped highlightOnHover withTableBorder withColumnBorders verticalSpacing="sm">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Kid</Table.Th>
                    <Table.Th>Chore</Table.Th>
                    <Table.Th>Submitted</Table.Th>
                    <Table.Th ta="right">Points</Table.Th>
                    <Table.Th ta="center">Action</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {pendingSubmissions.map((submission) => (
                    <Table.Tr key={submission.id}>
                      <Table.Td>{submission.kid_username}</Table.Td>
                      <Table.Td>
                        <Stack gap="xs">
                          <Text fw={500}>{submission.chore_name}</Text>
                          {submission.submission_notes && (
                            <Text size="sm" c="dimmed">
                              Note: {submission.submission_notes}
                            </Text>
                          )}
                        </Stack>
                      </Table.Td>
                      <Table.Td>{formatDate(submission.submitted_at!)}</Table.Td>
                      <Table.Td ta="right">
                        <Badge color="green" variant="light">
                          {submission.points_value}
                        </Badge>
                      </Table.Td>
                      <Table.Td ta="center">
                        <Button
                          size="xs"
                          variant="light"
                          color="blue"
                          onClick={() => openReviewModal(submission)}
                          leftSection={<IconEye size={14} />}
                        >
                          Review
                        </Button>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </ScrollArea>
          </Paper>
        )}

        {/* All Assignments */}
        <Paper shadow="md" radius="md" withBorder>
          <Group p="md" bg="blue.0">
            <Title order={4} c="blue.7">
              All Assignments ({assignments.length})
            </Title>
          </Group>
          {assignments.length === 0 ? (
            <Text ta="center" py="xl" c="dimmed">
              No chores have been assigned yet.
            </Text>
          ) : (
            <ScrollArea>
              <Table striped highlightOnHover withTableBorder withColumnBorders verticalSpacing="sm">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Kid</Table.Th>
                    <Table.Th>Chore</Table.Th>
                    <Table.Th>Assigned</Table.Th>
                    <Table.Th>Due Date</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th ta="right">Points</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {assignments.map((assignment) => (
                    <Table.Tr key={assignment.id}>
                      <Table.Td>{assignment.kid_username}</Table.Td>
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
                      <Table.Td>{formatDate(assignment.created_at)}</Table.Td>
                      <Table.Td>
                        {assignment.due_date ? (
                          <Group gap="xs">
                            <IconCalendar size={14} />
                            <Text size="sm">
                              {formatDate(assignment.due_date)}
                            </Text>
                          </Group>
                        ) : (
                          <Text size="sm" c="dimmed">
                            No deadline
                          </Text>
                        )}
                      </Table.Td>
                      <Table.Td>{getStatusBadge(assignment.assignment_status)}</Table.Td>
                      <Table.Td ta="right">
                        <Badge color="green" variant="light">
                          {assignment.points_value}
                        </Badge>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </ScrollArea>
          )}
        </Paper>
      </Stack>

      {/* Assign Chore Modal */}
      <Modal
        opened={assignModalOpen}
        onClose={() => setAssignModalOpen(false)}
        title="Assign Chore to Kid"
        centered
        size="md"
      >
        <form onSubmit={form.onSubmit(handleAssignChore)}>
          <Stack>
            <Select
              label="Select Chore"
              placeholder="Choose a chore to assign"
              data={chores.map(chore => ({
                value: chore.id,
                label: `${chore.name} (${chore.points_value} pts)`
              }))}
              {...form.getInputProps('chore_id')}
              searchable
            />

            <Select
              label="Assign to Kid"
              placeholder="Choose a kid"
              data={kids.map(kid => ({
                value: kid.id,
                label: kid.username
              }))}
              {...form.getInputProps('assigned_to_kid_id')}
              searchable
            />

            <DatePickerInput
              label="Due Date (Optional)"
              placeholder="Pick a due date"
              value={form.values.due_date ? new Date(form.values.due_date) : null}
              onChange={(date: any) => {
                if (date) {
                  const dateStr = date instanceof Date ? date.toISOString().split('T')[0] : date;
                  form.setFieldValue('due_date', dateStr);
                } else {
                  form.setFieldValue('due_date', '');
                }
              }}
              clearable
              minDate={new Date()}
            />

            <Textarea
              label="Notes (Optional)"
              placeholder="Add any special instructions or notes"
              {...form.getInputProps('notes')}
              minRows={3}
            />

            <Group justify="flex-end" mt="md">
              <Button variant="default" onClick={() => setAssignModalOpen(false)} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button type="submit" loading={isSubmitting} color="blue">
                Assign Chore
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>

      {/* Review Submission Modal */}
      <Modal
        opened={reviewModalOpen}
        onClose={() => setReviewModalOpen(false)}
        title="Review Assignment Submission"
        centered
        size="md"
      >
        {selectedSubmission && (
          <Stack>
            <Paper withBorder p="md" bg="gray.0">
              <Text fw={500}>{selectedSubmission.chore_name}</Text>
              <Text size="sm" c="dimmed">
                Submitted by: {selectedSubmission.kid_username}
              </Text>
              <Text size="sm" c="dimmed">
                Worth {selectedSubmission.points_value} points
              </Text>
              {selectedSubmission.due_date && (
                <Text size="sm" c="dimmed">
                  Due: {formatDate(selectedSubmission.due_date)}
                </Text>
              )}
            </Paper>

            {selectedSubmission.notes && (
              <Paper withBorder p="md">
                <Text fw={500} size="sm" mb="xs">Assignment Instructions:</Text>
                <Text size="sm">{selectedSubmission.notes}</Text>
              </Paper>
            )}

            {selectedSubmission.submission_notes && (
              <Paper withBorder p="md">
                <Text fw={500} size="sm" mb="xs">Kid's Submission Notes:</Text>
                <Text size="sm">{selectedSubmission.submission_notes}</Text>
              </Paper>
            )}

            <Group justify="flex-end" mt="md">
              <Button variant="default" onClick={() => setReviewModalOpen(false)} disabled={isSubmitting}>
                Close
              </Button>
              <Button
                color="red"
                onClick={() => handleSubmissionAction(selectedSubmission.id, 'reject')}
                loading={isSubmitting}
              >
                Reject
              </Button>
              <Button
                color="green"
                onClick={() => handleSubmissionAction(selectedSubmission.id, 'approve')}
                loading={isSubmitting}
              >
                Approve
              </Button>
            </Group>
          </Stack>
        )}
      </Modal>
    </Container>
  );
};

export default AssignChoresPage;

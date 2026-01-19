import React, { useState, useEffect } from 'react';
import * as api from '../services/api';
import { PetWithAge, PetHealthLog, PetHealthLogCreate, CareRecommendation } from '../services/api';
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
  NumberInput,
  Textarea,
  Select,
  Table,
  ScrollArea,
  Progress,
} from '@mantine/core';
import { IconHeartbeat, IconAlertCircle, IconCircleCheck, IconPlus, IconScale } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';

const WEIGHT_STATUS_COLORS: Record<string, string> = {
  healthy: 'green',
  underweight: 'yellow',
  overweight: 'orange',
};

const PetHealthPage: React.FC = () => {
  const [pets, setPets] = useState<PetWithAge[]>([]);
  const [selectedPetId, setSelectedPetId] = useState<string | null>(null);
  const [healthLogs, setHealthLogs] = useState<PetHealthLog[]>([]);
  const [careRec, setCareRec] = useState<CareRecommendation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [modalOpened, setModalOpened] = useState(false);
  const [weightGrams, setWeightGrams] = useState<number | ''>(0);
  const [notes, setNotes] = useState('');

  const fetchPets = async () => {
    try {
      const response = await api.getPets();
      setPets(response.data.filter(p => p.is_active));
    } catch (err) {
      console.error('Failed to fetch pets:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchHealthLogs = async (petId: string) => {
    try {
      const [logsResponse, recResponse] = await Promise.all([
        api.getPetHealthLogs(petId),
        api.getPetCareRecommendations(petId),
      ]);
      setHealthLogs(logsResponse.data);
      setCareRec(recResponse.data);
    } catch (err) {
      console.error('Failed to fetch health logs:', err);
    }
  };

  useEffect(() => {
    fetchPets();
  }, []);

  useEffect(() => {
    if (selectedPetId) {
      fetchHealthLogs(selectedPetId);
    } else {
      setHealthLogs([]);
      setCareRec(null);
    }
  }, [selectedPetId]);

  const handleOpenModal = () => {
    setWeightGrams(0);
    setNotes('');
    setModalOpened(true);
    setError(null);
  };

  const handleSubmitLog = async () => {
    if (!selectedPetId || !weightGrams) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const data: PetHealthLogCreate = {
        pet_id: selectedPetId,
        weight_grams: Number(weightGrams),
        notes: notes.trim() || undefined,
      };
      await api.createPetHealthLog(selectedPetId, data);
      notifications.show({
        title: 'Success',
        message: 'Health log recorded!',
        color: 'green',
        icon: <IconCircleCheck />,
      });
      fetchHealthLogs(selectedPetId);
      setModalOpened(false);
    } catch (err: any) {
      const apiError = err.response?.data?.detail || 'Failed to record health log.';
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

  const selectedPet = pets.find(p => p.id === selectedPetId);
  const latestLog = healthLogs[0];

  const getWeightProgress = () => {
    if (!careRec || !latestLog) return null;
    const [min, max] = careRec.healthy_weight_range_grams;
    const weight = latestLog.weight_grams;

    if (weight < min) {
      return { value: (weight / min) * 50, color: 'yellow' };
    } else if (weight > max) {
      return { value: Math.min(100, 50 + ((weight - min) / (max - min)) * 50), color: 'orange' };
    } else {
      return { value: 50 + ((weight - min) / (max - min)) * 50, color: 'green' };
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
        <Group justify="space-between">
          <Title order={2}>
            <IconHeartbeat size={28} style={{ marginRight: 8, verticalAlign: 'middle' }} />
            Pet Health Tracking
          </Title>
          {selectedPetId && (
            <Button leftSection={<IconPlus size={18} />} onClick={handleOpenModal}>
              Log Weight
            </Button>
          )}
        </Group>

        {error && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" withCloseButton onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Select
          label="Select Pet"
          placeholder="Choose a pet to view health records"
          data={pets.map(p => ({ value: p.id, label: p.name }))}
          value={selectedPetId}
          onChange={setSelectedPetId}
          clearable
        />

        {!selectedPetId && pets.length > 0 && (
          <Paper p="lg" shadow="xs" withBorder>
            <Text ta="center">Select a pet to view and log health records.</Text>
          </Paper>
        )}

        {pets.length === 0 && (
          <Paper p="lg" shadow="xs" withBorder>
            <Text ta="center">No pets found. Add a pet first to track health.</Text>
          </Paper>
        )}

        {selectedPet && careRec && (
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Stack gap="md">
              <Group justify="space-between">
                <div>
                  <Title order={4}>{selectedPet.name}</Title>
                  <Text size="sm" c="dimmed">
                    {selectedPet.life_stage.replace('_', ' ')} - {selectedPet.age_months} months old
                  </Text>
                </div>
                {latestLog && (
                  <Badge size="lg" color={WEIGHT_STATUS_COLORS[latestLog.weight_status || 'healthy']}>
                    {latestLog.weight_grams}g - {latestLog.weight_status}
                  </Badge>
                )}
              </Group>

              <Paper p="md" withBorder>
                <Group justify="space-between" mb="xs">
                  <Text size="sm" fw={500}>Healthy Weight Range</Text>
                  <Text size="sm" c="dimmed">
                    {careRec.healthy_weight_range_grams[0]}g - {careRec.healthy_weight_range_grams[1]}g
                  </Text>
                </Group>
                {getWeightProgress() && (
                  <Progress
                    value={getWeightProgress()!.value}
                    color={getWeightProgress()!.color}
                    size="lg"
                  />
                )}
                {latestLog && (
                  <Text size="xs" c="dimmed" mt="xs" ta="center">
                    Last recorded: {latestLog.weight_grams}g on {new Date(latestLog.logged_at).toLocaleDateString()}
                  </Text>
                )}
              </Paper>
            </Stack>
          </Card>
        )}

        {selectedPetId && healthLogs.length > 0 && (
          <>
            <Title order={4} c="dimmed" mt="xl">Weight History</Title>
            <Paper shadow="md" radius="md" withBorder>
              <ScrollArea>
                <Table striped highlightOnHover withTableBorder verticalSpacing="sm">
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Date</Table.Th>
                      <Table.Th>Weight</Table.Th>
                      <Table.Th>Status</Table.Th>
                      <Table.Th>Life Stage</Table.Th>
                      <Table.Th>Logged By</Table.Th>
                      <Table.Th>Notes</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {healthLogs.map((log) => (
                      <Table.Tr key={log.id}>
                        <Table.Td>{new Date(log.logged_at).toLocaleDateString()}</Table.Td>
                        <Table.Td fw={500}>{log.weight_grams}g</Table.Td>
                        <Table.Td>
                          <Badge color={WEIGHT_STATUS_COLORS[log.weight_status || 'healthy']}>
                            {log.weight_status || 'N/A'}
                          </Badge>
                        </Table.Td>
                        <Table.Td>
                          <Badge variant="light">{log.life_stage_at_log?.replace('_', ' ') || 'N/A'}</Badge>
                        </Table.Td>
                        <Table.Td>{log.logged_by_username}</Table.Td>
                        <Table.Td>{log.notes || '-'}</Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </ScrollArea>
            </Paper>
          </>
        )}

        {selectedPetId && healthLogs.length === 0 && (
          <Paper p="lg" shadow="xs" withBorder>
            <Text ta="center">No health logs recorded yet. Click "Log Weight" to start tracking.</Text>
          </Paper>
        )}
      </Stack>

      <Modal
        opened={modalOpened}
        onClose={() => setModalOpened(false)}
        title={`Log Weight for ${selectedPet?.name}`}
        centered
        size="md"
      >
        <Stack>
          {careRec && (
            <Alert color="blue" variant="light">
              Healthy range for {careRec.life_stage.replace('_', ' ')}: {careRec.healthy_weight_range_grams[0]}g - {careRec.healthy_weight_range_grams[1]}g
            </Alert>
          )}
          <NumberInput
            required
            label="Weight (grams)"
            placeholder="e.g., 150"
            min={1}
            max={2000}
            value={weightGrams}
            onChange={(val) => setWeightGrams(typeof val === 'number' ? val : '')}
            leftSection={<IconScale size={16} />}
          />
          <Textarea
            label="Notes (Optional)"
            placeholder="Any observations about the pet's health"
            value={notes}
            onChange={(e) => setNotes(e.currentTarget.value)}
            minRows={2}
          />
          <Group justify="flex-end" mt="md">
            <Button variant="default" onClick={() => setModalOpened(false)} disabled={isSubmitting}>
              Cancel
            </Button>
            <Button onClick={handleSubmitLog} loading={isSubmitting} disabled={!weightGrams}>
              Save Log
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
};

export default PetHealthPage;

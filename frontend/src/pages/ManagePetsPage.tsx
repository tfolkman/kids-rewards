import React, { useState, useEffect } from 'react';
import * as api from '../services/api';
import { PetWithAge, PetCreate, PetSpecies } from '../services/api';
import {
  Button,
  Modal,
  TextInput,
  Textarea,
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
  Card,
  Image,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { DatePickerInput } from '@mantine/dates';
import { IconPencil, IconCircleOff, IconDotsVertical, IconPlus, IconAlertCircle, IconCircleCheck, IconPaw } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';

const LIFE_STAGE_COLORS: Record<string, string> = {
  baby: 'pink',
  juvenile: 'yellow',
  sub_adult: 'orange',
  adult: 'green',
};

const ManagePetsPage: React.FC = () => {
  const [pets, setPets] = useState<PetWithAge[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [modalOpened, setModalOpened] = useState(false);
  const [editingPet, setEditingPet] = useState<PetWithAge | null>(null);
  const [confirmDeactivateModalOpen, setConfirmDeactivateModalOpen] = useState(false);
  const [petToDeactivate, setPetToDeactivate] = useState<PetWithAge | null>(null);

  const form = useForm<PetCreate>({
    initialValues: {
      name: '',
      species: 'bearded_dragon' as PetSpecies,
      birthday: new Date().toISOString().split('T')[0],
      photo_url: '',
      care_notes: '',
    },
    validate: {
      name: (value: string) => (value.trim().length > 0 ? null : 'Pet name is required'),
      birthday: (value: string) => (value ? null : 'Birthday is required'),
    },
  });

  const fetchPets = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.getPets();
      setPets(response.data);
    } catch (err) {
      setError('Failed to fetch pets.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPets();
  }, []);

  const handleOpenModal = (pet: PetWithAge | null = null) => {
    setEditingPet(pet);
    if (pet) {
      form.setValues({
        name: pet.name,
        species: pet.species,
        birthday: pet.birthday.split('T')[0],
        photo_url: pet.photo_url || '',
        care_notes: pet.care_notes || '',
      });
    } else {
      form.reset();
    }
    setModalOpened(true);
    setError(null);
  };

  const handleCloseModal = () => {
    setModalOpened(false);
    setEditingPet(null);
    form.reset();
  };

  const handleSubmitPet = async (values: PetCreate) => {
    setIsSubmitting(true);
    setError(null);
    try {
      const payload = {
        ...values,
        birthday: new Date(values.birthday).toISOString(),
      };
      if (editingPet) {
        await api.updatePet(editingPet.id, payload);
        notifications.show({
          title: 'Success',
          message: 'Pet updated successfully!',
          color: 'green',
          icon: <IconCircleCheck />,
        });
      } else {
        await api.createPet(payload);
        notifications.show({
          title: 'Success',
          message: 'Pet created successfully!',
          color: 'green',
          icon: <IconCircleCheck />,
        });
      }
      fetchPets();
      handleCloseModal();
    } catch (err: any) {
      const apiError = err.response?.data?.detail || (editingPet ? 'Failed to update pet.' : 'Failed to create pet.');
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

  const openDeactivateConfirmModal = (pet: PetWithAge) => {
    setPetToDeactivate(pet);
    setConfirmDeactivateModalOpen(true);
  };

  const handleDeactivatePet = async () => {
    if (!petToDeactivate) return;
    setIsSubmitting(true);
    try {
      await api.deactivatePet(petToDeactivate.id);
      notifications.show({
        title: 'Success',
        message: 'Pet deactivated successfully!',
        color: 'green',
        icon: <IconCircleCheck />,
      });
      fetchPets();
      setConfirmDeactivateModalOpen(false);
      setPetToDeactivate(null);
    } catch (err: any) {
      const apiError = err.response?.data?.detail || 'Failed to deactivate pet.';
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

  if (isLoading && pets.length === 0) {
    return (
      <Container size="md" py="xl" style={{ display: 'flex', justifyContent: 'center' }}>
        <Loader />
      </Container>
    );
  }

  const activePets = pets.filter(p => p.is_active);
  const inactivePets = pets.filter(p => !p.is_active);

  return (
    <Container size="lg" py="xl">
      <Stack gap="lg">
        <Group justify="space-between">
          <Title order={2}>
            <IconPaw size={28} style={{ marginRight: 8, verticalAlign: 'middle' }} />
            Manage Pets
          </Title>
          <Button leftSection={<IconPlus size={18} />} onClick={() => handleOpenModal()}>
            Add New Pet
          </Button>
        </Group>

        {error && !modalOpened && (
          <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" withCloseButton onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {pets.length === 0 && !isLoading && (
          <Paper p="lg" shadow="xs" withBorder>
            <Text ta="center">No pets added yet. Click "Add New Pet" to get started.</Text>
          </Paper>
        )}

        {activePets.length > 0 && (
          <>
            <Title order={4} c="dimmed">Active Pets</Title>
            <Group gap="md">
              {activePets.map((pet) => (
                <Card key={pet.id} shadow="sm" padding="lg" radius="md" withBorder style={{ width: 300 }}>
                  {pet.photo_url && (
                    <Card.Section>
                      <Image src={pet.photo_url} height={160} alt={pet.name} />
                    </Card.Section>
                  )}
                  <Group justify="space-between" mt="md" mb="xs">
                    <Text fw={500}>{pet.name}</Text>
                    <Badge color={LIFE_STAGE_COLORS[pet.life_stage] || 'gray'}>
                      {pet.life_stage.replace('_', ' ')}
                    </Badge>
                  </Group>
                  <Text size="sm" c="dimmed">
                    Age: {pet.age_months} months
                  </Text>
                  <Text size="sm" c="dimmed">
                    Birthday: {new Date(pet.birthday).toLocaleDateString()}
                  </Text>
                  {pet.care_notes && (
                    <Text size="xs" c="dimmed" mt="xs">
                      {pet.care_notes}
                    </Text>
                  )}
                  <Group mt="md">
                    <Button variant="light" size="xs" onClick={() => handleOpenModal(pet)}>
                      <IconPencil size={14} />
                    </Button>
                    <Button variant="light" color="orange" size="xs" onClick={() => openDeactivateConfirmModal(pet)}>
                      <IconCircleOff size={14} />
                    </Button>
                  </Group>
                </Card>
              ))}
            </Group>
          </>
        )}

        {inactivePets.length > 0 && (
          <>
            <Title order={4} c="dimmed" mt="xl">Inactive Pets</Title>
            <Paper shadow="md" radius="md" withBorder>
              <ScrollArea>
                <Table striped highlightOnHover withTableBorder verticalSpacing="sm">
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Name</Table.Th>
                      <Table.Th>Species</Table.Th>
                      <Table.Th>Age</Table.Th>
                      <Table.Th>Status</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {inactivePets.map((pet) => (
                      <Table.Tr key={pet.id}>
                        <Table.Td>{pet.name}</Table.Td>
                        <Table.Td>{pet.species.replace('_', ' ')}</Table.Td>
                        <Table.Td>{pet.age_months} months</Table.Td>
                        <Table.Td>
                          <Badge color="gray">Inactive</Badge>
                        </Table.Td>
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
        title={editingPet ? 'Edit Pet' : 'Add New Pet'}
        centered
        size="md"
      >
        <form onSubmit={form.onSubmit(handleSubmitPet)}>
          <Stack>
            {error && modalOpened && (
              <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" withCloseButton onClose={() => setError(null)}>
                {error}
              </Alert>
            )}
            <TextInput
              required
              label="Pet Name"
              placeholder="e.g., Spike"
              {...form.getInputProps('name')}
            />
            <TextInput
              required
              label="Birthday"
              type="date"
              {...form.getInputProps('birthday')}
            />
            <TextInput
              label="Photo URL (Optional)"
              placeholder="https://..."
              {...form.getInputProps('photo_url')}
            />
            <Textarea
              label="Care Notes (Optional)"
              placeholder="Any special care requirements"
              {...form.getInputProps('care_notes')}
              minRows={2}
            />
            <Group justify="flex-end" mt="md">
              <Button variant="default" onClick={handleCloseModal} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button type="submit" loading={isSubmitting}>
                {editingPet ? 'Update Pet' : 'Create Pet'}
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
        <Text>Are you sure you want to deactivate {petToDeactivate?.name}?</Text>
        <Group justify="flex-end" mt="lg">
          <Button variant="default" onClick={() => setConfirmDeactivateModalOpen(false)} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button color="orange" onClick={handleDeactivatePet} loading={isSubmitting}>
            Deactivate
          </Button>
        </Group>
      </Modal>
    </Container>
  );
};

export default ManagePetsPage;

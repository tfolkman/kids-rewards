import React, { useState, useEffect } from 'react';
import * as api from '../services/api';
import { PetOverviewItem, PetCareOverview } from '../services/api';
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
  Image,
  List,
  Progress,
  SimpleGrid,
  ThemeIcon,
} from '@mantine/core';
import { IconPaw, IconAlertCircle, IconHeartbeat, IconSalad, IconFlame, IconScale } from '@tabler/icons-react';

const LIFE_STAGE_COLORS: Record<string, string> = {
  baby: 'pink',
  juvenile: 'yellow',
  sub_adult: 'orange',
  adult: 'green',
};

const WEIGHT_STATUS_COLORS: Record<string, string> = {
  healthy: 'green',
  underweight: 'yellow',
  overweight: 'orange',
};

const PetCareOverviewPage: React.FC = () => {
  const [overview, setOverview] = useState<PetOverviewItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchOverview = async () => {
      try {
        const response = await api.getPetCareOverview();
        setOverview(response.data.pets);
      } catch (err) {
        setError('Failed to fetch pet care overview.');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };
    fetchOverview();
  }, []);

  if (isLoading) {
    return (
      <Container size="md" py="xl" style={{ display: 'flex', justifyContent: 'center' }}>
        <Loader />
      </Container>
    );
  }

  if (error) {
    return (
      <Container size="md" py="xl">
        <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red">
          {error}
        </Alert>
      </Container>
    );
  }

  if (overview.length === 0) {
    return (
      <Container size="md" py="xl">
        <Paper p="lg" shadow="xs" withBorder>
          <Text ta="center">No pets found. Add a pet to see the overview.</Text>
        </Paper>
      </Container>
    );
  }

  return (
    <Container size="xl" py="xl">
      <Stack gap="xl">
        <Title order={2}>
          <IconPaw size={28} style={{ marginRight: 8, verticalAlign: 'middle' }} />
          Pet Care Overview
        </Title>

        {overview.map((item) => (
          <Card key={item.pet.id} shadow="sm" padding="lg" radius="md" withBorder>
            <Group align="flex-start" gap="xl">
              {item.pet.photo_url && (
                <Image
                  src={item.pet.photo_url}
                  height={150}
                  width={150}
                  radius="md"
                  alt={item.pet.name}
                  style={{ objectFit: 'cover' }}
                />
              )}
              <Stack gap="sm" style={{ flex: 1 }}>
                <Group justify="space-between">
                  <div>
                    <Title order={3}>{item.pet.name}</Title>
                    <Text size="sm" c="dimmed">
                      {item.pet.species.replace('_', ' ')} - {item.pet.age_months} months old
                    </Text>
                  </div>
                  <Badge size="lg" color={LIFE_STAGE_COLORS[item.pet.life_stage] || 'gray'}>
                    {item.pet.life_stage.replace('_', ' ')}
                  </Badge>
                </Group>

                <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="md">
                  <Paper p="sm" withBorder>
                    <Group gap="xs">
                      <ThemeIcon color="blue" variant="light">
                        <IconSalad size={16} />
                      </ThemeIcon>
                      <Text size="sm" fw={500}>Feeding</Text>
                    </Group>
                    <Text size="sm" mt="xs">{item.care_recommendations.feeding_frequency}</Text>
                  </Paper>

                  <Paper p="sm" withBorder>
                    <Group gap="xs">
                      <ThemeIcon color="green" variant="light">
                        <IconFlame size={16} />
                      </ThemeIcon>
                      <Text size="sm" fw={500}>Diet</Text>
                    </Group>
                    <Text size="sm" mt="xs">{item.care_recommendations.diet_ratio}</Text>
                  </Paper>

                  <Paper p="sm" withBorder>
                    <Group gap="xs">
                      <ThemeIcon color="orange" variant="light">
                        <IconScale size={16} />
                      </ThemeIcon>
                      <Text size="sm" fw={500}>Weight Range</Text>
                    </Group>
                    <Text size="sm" mt="xs">
                      {item.care_recommendations.healthy_weight_range_grams[0]}g - {item.care_recommendations.healthy_weight_range_grams[1]}g
                    </Text>
                    {item.latest_weight && (
                      <Badge
                        size="sm"
                        color={WEIGHT_STATUS_COLORS[item.latest_weight.weight_status || 'healthy']}
                        mt="xs"
                      >
                        Last: {item.latest_weight.weight_grams}g ({item.latest_weight.weight_status})
                      </Badge>
                    )}
                  </Paper>

                  <Paper p="sm" withBorder>
                    <Group gap="xs">
                      <ThemeIcon color="violet" variant="light">
                        <IconHeartbeat size={16} />
                      </ThemeIcon>
                      <Text size="sm" fw={500}>Tasks</Text>
                    </Group>
                    <Group gap="xs" mt="xs">
                      <Badge color="blue" variant="light">{item.pending_tasks} pending</Badge>
                      <Badge color="yellow" variant="light">{item.awaiting_approval} awaiting</Badge>
                    </Group>
                  </Paper>
                </SimpleGrid>

                <Paper p="sm" withBorder>
                  <Text size="sm" fw={500} mb="xs">Care Tips</Text>
                  <List size="sm" spacing="xs">
                    {item.care_recommendations.care_tips.map((tip, index) => (
                      <List.Item key={index}>{tip}</List.Item>
                    ))}
                  </List>
                </Paper>
              </Stack>
            </Group>
          </Card>
        ))}
      </Stack>
    </Container>
  );
};

export default PetCareOverviewPage;

import React, { useEffect, useState } from 'react';
import { Group, Text, Card, Stack, Loader, Center, ThemeIcon, Badge, Tooltip, Paper } from '@mantine/core';
import { IconFlame, IconTrendingUp, IconCalendarEvent } from '@tabler/icons-react';
import { showNotification } from '@mantine/notifications';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'https://nb8fzkab80.execute-api.us-west-2.amazonaws.com/prod';

interface StreakData {
  current_streak: number;
  longest_streak: number;
  last_completion_date: string | null;
  streak_active: boolean;
}

interface StreakDisplayProps {
  compact?: boolean;
}

export const StreakDisplay: React.FC<StreakDisplayProps> = ({ compact = false }) => {
  const [streakData, setStreakData] = useState<StreakData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStreakData();
  }, []);

  const fetchStreakData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/kids/streak/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        }
      });
      setStreakData(response.data);
    } catch (error) {
      console.error('Error fetching streak data:', error);
      showNotification({
        title: 'Error',
        message: 'Could not load streak data',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Center h={compact ? 50 : 100}>
        <Loader size="sm" />
      </Center>
    );
  }

  if (!streakData) {
    return null;
  }

  const getStreakColor = (streak: number) => {
    if (streak === 0) return 'gray';
    if (streak < 3) return 'orange';
    if (streak < 7) return 'yellow';
    if (streak < 14) return 'teal';
    if (streak < 30) return 'blue';
    return 'grape';
  };

  const getStreakMessage = (streak: number) => {
    if (streak === 0) return 'Start your streak today!';
    if (streak === 1) return 'Great start! Keep it up!';
    if (streak < 3) return `${3 - streak} more days to earn 10 bonus points!`;
    if (streak < 7) return `${7 - streak} more days to earn 25 bonus points!`;
    if (streak < 14) return `${14 - streak} more days to earn 50 bonus points!`;
    if (streak < 30) return `${30 - streak} more days to earn 100 bonus points!`;
    return 'Amazing streak! Keep going!';
  };

  if (compact) {
    return (
      <Tooltip
        label={
          <Stack gap={5}>
            <Text size="sm">Current streak: {streakData.current_streak} days</Text>
            <Text size="sm">Longest streak: {streakData.longest_streak} days</Text>
            <Text size="xs" c="dimmed">{getStreakMessage(streakData.current_streak)}</Text>
          </Stack>
        }
        position="bottom"
        withArrow
      >
        <Badge
          size="lg"
          radius="sm"
          variant={streakData.streak_active ? 'filled' : 'light'}
          color={getStreakColor(streakData.current_streak)}
          leftSection={
            <IconFlame size={16} style={{ marginTop: 2 }} />
          }
        >
          {streakData.current_streak}
        </Badge>
      </Tooltip>
    );
  }

  return (
    <Card shadow="sm" p="lg" radius="md" withBorder>
      <Stack gap="md">
        <Group justify="space-between">
          <Text fw={500} size="lg">Chore Streak</Text>
          {!streakData.streak_active && streakData.current_streak > 0 && (
            <Badge color="red" variant="light">
              Streak at risk!
            </Badge>
          )}
        </Group>

        <Group grow>
          <Paper p="md" radius="md" withBorder>
            <Stack gap="xs" align="center">
              <ThemeIcon
                size="xl"
                radius="xl"
                variant={streakData.streak_active ? 'filled' : 'light'}
                color={getStreakColor(streakData.current_streak)}
              >
                <IconFlame size={24} />
              </ThemeIcon>
              <Text size="xl" fw={700} color={getStreakColor(streakData.current_streak)}>
                {streakData.current_streak}
              </Text>
              <Text size="xs" c="dimmed">Current Streak</Text>
            </Stack>
          </Paper>

          <Paper p="md" radius="md" withBorder>
            <Stack gap="xs" align="center">
              <ThemeIcon size="xl" radius="xl" variant="light" color="blue">
                <IconTrendingUp size={24} />
              </ThemeIcon>
              <Text size="xl" fw={700}>
                {streakData.longest_streak}
              </Text>
              <Text size="xs" c="dimmed">Longest Streak</Text>
            </Stack>
          </Paper>
        </Group>

        <Stack gap="xs">
          <Group gap="xs">
            <IconCalendarEvent size={16} />
            <Text size="sm" c="dimmed">
              {streakData.last_completion_date
                ? `Last completed: ${new Date(streakData.last_completion_date).toLocaleDateString()}`
                : 'No chores completed yet'}
            </Text>
          </Group>

          <Text size="sm" fw={500} color={getStreakColor(streakData.current_streak)}>
            {getStreakMessage(streakData.current_streak)}
          </Text>
        </Stack>

        <Stack gap={5}>
          <Text size="xs" fw={500}>Streak Milestones:</Text>
          <Group gap="xs">
            <Badge color={streakData.current_streak >= 3 ? 'green' : 'gray'} variant="dot">
              3 days = 10 pts
            </Badge>
            <Badge color={streakData.current_streak >= 7 ? 'green' : 'gray'} variant="dot">
              7 days = 25 pts
            </Badge>
            <Badge color={streakData.current_streak >= 14 ? 'green' : 'gray'} variant="dot">
              14 days = 50 pts
            </Badge>
            <Badge color={streakData.current_streak >= 30 ? 'green' : 'gray'} variant="dot">
              30 days = 100 pts
            </Badge>
          </Group>
        </Stack>
      </Stack>
    </Card>
  );
};
import React, { useEffect, useState, useMemo } from 'react';
import { 
  Card, 
  Stack, 
  Group, 
  Text, 
  Progress, 
  Badge, 
  Paper, 
  ThemeIcon,
  SimpleGrid,
  Center,
  Loader,
  Title,
  Box,
  Tooltip
} from '@mantine/core';
import { 
  IconTarget, 
  IconClock, 
  IconTrendingUp,
  IconSparkles
} from '@tabler/icons-react';
import type { PurchaseLog } from '../services/api';

interface BeardedDragonGoalProps {
  purchases: PurchaseLog[];
  loading?: boolean;
}

const GOAL_AMOUNT = 15750;
const POINTS_PER_PURCHASE = 875;
const DEADLINE = new Date('2025-12-31T23:59:59');
const BEARDED_DRAGON_ITEM_ID = '4d35256f-f226-43d7-8211-627891059ebf';

// Kid colors for visual distinction
const KID_COLORS: Record<string, string> = {
  clara: 'blue',
  emery: 'green', 
  aiden: 'orange'
};

export const BeardedDragonGoal: React.FC<BeardedDragonGoalProps> = ({ purchases, loading = false }) => {
  const [timeRemaining, setTimeRemaining] = useState<string>('');
  const [daysLeft, setDaysLeft] = useState<number>(0);

  // Calculate progress
  const progressData = useMemo(() => {
    const validPurchases = purchases.filter(
      p => p.item_id === BEARDED_DRAGON_ITEM_ID && 
      ['approved', 'completed'].includes(p.status)
    );

    const kidContributions: Record<string, number> = {};
    let totalPoints = 0;

    validPurchases.forEach(purchase => {
      const username = purchase.username.toLowerCase();
      if (!kidContributions[username]) {
        kidContributions[username] = 0;
      }
      kidContributions[username] += POINTS_PER_PURCHASE;
      totalPoints += POINTS_PER_PURCHASE;
    });

    const percentage = Math.min((totalPoints / GOAL_AMOUNT) * 100, 100);
    const purchasesNeeded = Math.ceil((GOAL_AMOUNT - totalPoints) / POINTS_PER_PURCHASE);

    return {
      totalPoints,
      percentage,
      purchasesNeeded,
      kidContributions,
      validPurchases: validPurchases.length
    };
  }, [purchases]);

  // Update countdown timer
  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date();
      const diff = DEADLINE.getTime() - now.getTime();
      
      if (diff <= 0) {
        setTimeRemaining('Goal deadline reached!');
        setDaysLeft(0);
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      
      setDaysLeft(days);
      setTimeRemaining(`${days} days, ${hours} hours, ${minutes} minutes`);
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  // Get milestone message
  const getMilestoneMessage = () => {
    const { percentage, purchasesNeeded } = progressData;
    
    if (percentage === 0) return "Let's start saving for our Bearded Dragon! 🦎";
    if (percentage < 25) return `Great start! Only ${purchasesNeeded} more purchases to go!`;
    if (percentage < 50) return `You're making progress! Keep saving!`;
    if (percentage < 75) return `Halfway there! The Bearded Dragon is getting closer!`;
    if (percentage < 100) return `Almost there! Just ${purchasesNeeded} more purchases!`;
    return "🎉 GOAL REACHED! Time to get your Bearded Dragon! 🦎";
  };

  // Get urgency color based on days remaining
  const getUrgencyColor = () => {
    if (daysLeft <= 7) return 'red';
    if (daysLeft <= 30) return 'orange';
    if (daysLeft <= 60) return 'yellow';
    return 'green';
  };

  if (loading) {
    return (
      <Center h={200}>
        <Loader size="lg" />
      </Center>
    );
  }

  return (
    <Stack gap="lg" className="fade-in">
      {/* Main Progress Card */}
      <Card shadow="lg" p="xl" radius="md" withBorder className="card-hover">
        <Stack gap="md">
          <Group justify="space-between">
            <Group>
              <ThemeIcon size="xl" radius="xl" variant="gradient" gradient={{ from: 'teal', to: 'lime' }}>
                <IconTarget size={28} />
              </ThemeIcon>
              <div>
                <Title order={3}>Bearded Dragon Savings Goal</Title>
                <Text size="sm" c="dimmed">Collective family goal</Text>
              </div>
            </Group>
            {progressData.percentage >= 100 && (
              <Badge size="lg" color="green" variant="filled" className="pulse">
                GOAL REACHED!
              </Badge>
            )}
          </Group>

          {/* Progress Bar */}
          <Box>
            <Group justify="space-between" mb="xs">
              <Text size="sm" fw={500}>Progress</Text>
              <Text size="sm" fw={500}>{progressData.percentage.toFixed(1)}%</Text>
            </Group>
            <Progress 
              size="xl" 
              radius="xl" 
              value={progressData.percentage}
              color={progressData.percentage >= 100 ? 'green' : 'teal'}
              animated
              styles={{
                root: { height: 30 }
              }}
            />
            <Group justify="space-between" mt="xs">
              <Text size="lg" fw={700} c="teal">
                ${progressData.totalPoints}
              </Text>
              <Text size="lg" fw={700} c="dimmed">
                ${GOAL_AMOUNT}
              </Text>
            </Group>
          </Box>

          {/* Milestone Message */}
          <Paper p="md" radius="md" withBorder bg="gray.0">
            <Group>
              <ThemeIcon size="lg" radius="xl" variant="light" color="yellow">
                <IconSparkles size={20} />
              </ThemeIcon>
              <Text size="sm" fw={500}>{getMilestoneMessage()}</Text>
            </Group>
          </Paper>

          {/* Countdown Timer */}
          <Paper p="md" radius="md" withBorder className={daysLeft <= 30 ? 'pulse' : ''}>
            <Group justify="space-between">
              <Group>
                <ThemeIcon size="lg" radius="xl" variant="light" color={getUrgencyColor()}>
                  <IconClock size={20} />
                </ThemeIcon>
                <div>
                  <Text size="xs" c="dimmed">Time Remaining</Text>
                  <Text size="sm" fw={600} c={getUrgencyColor()}>
                    {timeRemaining}
                  </Text>
                </div>
              </Group>
              <Badge size="lg" color={getUrgencyColor()} variant="light">
                {daysLeft} days
              </Badge>
            </Group>
          </Paper>
        </Stack>
      </Card>

      {/* Individual Contributions */}
      <Card shadow="sm" p="lg" radius="md" withBorder>
        <Stack gap="md">
          <Group>
            <ThemeIcon size="lg" radius="xl" variant="light" color="indigo">
              <IconTrendingUp size={20} />
            </ThemeIcon>
            <Title order={4}>Individual Contributions</Title>
          </Group>

          <SimpleGrid cols={{ base: 1, sm: 3 }} spacing="md">
            {['clara', 'emery', 'aiden'].map(kid => {
              const contribution = progressData.kidContributions[kid] || 0;
              const purchases = contribution / POINTS_PER_PURCHASE;
              const individualGoal = GOAL_AMOUNT / 3; // Each kid's share is 1/3 of total
              const individualPercentage = (contribution / individualGoal) * 100;
              const remainingForKid = Math.max(0, individualGoal - contribution);

              return (
                <Paper key={kid} p="md" radius="md" withBorder>
                  <Stack gap="xs" align="center">
                    <Badge size="lg" color={KID_COLORS[kid]} variant="light">
                      {kid.charAt(0).toUpperCase() + kid.slice(1)}
                    </Badge>
                    <Text size="2xl" fw={700} c={KID_COLORS[kid]}>
                      ${contribution}
                    </Text>
                    <Text size="xs" c="dimmed">
                      {purchases} purchase{purchases !== 1 ? 's' : ''}
                    </Text>
                    <Progress 
                      size="sm" 
                      radius="xl" 
                      value={Math.min(100, individualPercentage)}
                      color={KID_COLORS[kid]}
                      style={{ width: '100%' }}
                    />
                    <Text size="xs" c="dimmed">
                      {individualPercentage.toFixed(1)}% of their ${individualGoal.toFixed(0)} goal
                    </Text>
                    <Text size="xs" fw={500} c={remainingForKid > 0 ? 'orange' : 'green'}>
                      {remainingForKid > 0 
                        ? `$${remainingForKid.toFixed(0)} remaining`
                        : '✓ Goal reached!'}
                    </Text>
                  </Stack>
                </Paper>
              );
            })}
          </SimpleGrid>
        </Stack>
      </Card>

      {/* Stats Summary */}
      <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="md">
        <Paper p="md" radius="md" withBorder>
          <Stack gap="xs" align="center">
            <Text size="xs" c="dimmed">Total Purchases</Text>
            <Text size="xl" fw={700}>{progressData.validPurchases}</Text>
          </Stack>
        </Paper>
        <Paper p="md" radius="md" withBorder>
          <Stack gap="xs" align="center">
            <Text size="xs" c="dimmed">Purchases Needed</Text>
            <Text size="xl" fw={700} c="teal">{progressData.purchasesNeeded}</Text>
          </Stack>
        </Paper>
        <Paper p="md" radius="md" withBorder>
          <Stack gap="xs" align="center">
            <Text size="xs" c="dimmed">Points Remaining</Text>
            <Text size="xl" fw={700} c="orange">
              ${GOAL_AMOUNT - progressData.totalPoints}
            </Text>
          </Stack>
        </Paper>
        <Paper p="md" radius="md" withBorder>
          <Stack gap="xs" align="center">
            <Text size="xs" c="dimmed">Daily Rate Needed</Text>
            <Tooltip label="Points needed per day to reach goal">
              <Text size="xl" fw={700} c="blue">
                ${daysLeft > 0 ? Math.ceil((GOAL_AMOUNT - progressData.totalPoints) / daysLeft) : 0}
              </Text>
            </Tooltip>
          </Stack>
        </Paper>
      </SimpleGrid>
    </Stack>
  );
};
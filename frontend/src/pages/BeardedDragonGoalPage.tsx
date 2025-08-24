import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Title, 
  Alert, 
  Stack,
  Group,
  Text,
  Center,
  LoadingOverlay
} from '@mantine/core';
import { IconAlertCircle } from '@tabler/icons-react';
import { Navigate } from 'react-router-dom';
import { showNotification } from '@mantine/notifications';
import { BeardedDragonGoal } from '../components/BeardedDragonGoal';
import { getBeardedDragonPurchases } from '../services/api';
import type { PurchaseLog } from '../services/api';
import { useAuth } from '../App';

const BeardedDragonGoalPage: React.FC = () => {
  const [allPurchases, setAllPurchases] = useState<PurchaseLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { currentUser } = useAuth();

  useEffect(() => {
    if (!currentUser) {
      setError("You must be logged in to view this page.");
      setLoading(false);
      return;
    }

    fetchAllPurchaseData();
    
    // Set up auto-refresh every 30 seconds
    const refreshInterval = setInterval(() => {
      fetchAllPurchaseData(true);
    }, 30000);

    return () => clearInterval(refreshInterval);
  }, [currentUser]);

  const fetchAllPurchaseData = async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      
      // Fetch all three kids' bearded dragon purchases
      const response = await getBeardedDragonPurchases();
      
      setAllPurchases(response.data);
      setError(null);
      
      // Show notification on silent refresh if new purchases detected
      if (silent && response.data.length > allPurchases.length) {
        showNotification({
          title: 'Progress Updated!',
          message: 'New contribution detected!',
          color: 'teal',
        });
      }
    } catch (err) {
      if (!silent) {
        setError('Failed to load purchase data. Please try again.');
        console.error('Error fetching purchase data:', err);
      }
    } finally {
      if (!silent) setLoading(false);
    }
  };


  if (loading) {
    return (
      <Container size="xl" my="xl">
        <Center h={400}>
          <LoadingOverlay visible={true} />
        </Center>
      </Container>
    );
  }

  return (
    <Container size="xl" my="xl" className="page-container">
      <Stack gap="xl">
        {/* Header */}
        <Group justify="space-between">
          <div>
            <Title order={1} mb="xs">
              🦎 Bearded Dragon Savings Goal
            </Title>
            <Text c="dimmed">
              Track your collective progress toward getting a Bearded Dragon!
            </Text>
          </div>
        </Group>

        {/* Error Alert */}
        {error && (
          <Alert 
            icon={<IconAlertCircle size="1rem" />} 
            title="Error" 
            color="red" 
            radius="md"
          >
            {error}
          </Alert>
        )}

        {/* Main Goal Component */}
        {!error && (
          <>
            <BeardedDragonGoal 
              purchases={allPurchases} 
              loading={loading}
            />

            {/* Information Section */}
            <Alert 
              color="blue" 
              radius="md"
              title="How it works"
            >
              <Stack gap="xs">
                <Text size="sm">
                  • Each time you redeem the "$25 Bearded Dragon" item from the store, it counts toward your goal
                </Text>
                <Text size="sm">
                  • The group needs 18 total purchases (15,750 points) to reach the goal
                </Text>
                <Text size="sm">
                  • Each kid (Clara, Emery, and Aiden) needs to contribute 1/3 of the goal (5,250 points or 6 purchases)
                </Text>
                <Text size="sm">
                  • Complete the goal by December 31, 2025 to get your Bearded Dragon!
                </Text>
              </Stack>
            </Alert>

            {/* Note about data */}
            <Alert 
              color="yellow" 
              radius="md"
              title="Note"
            >
              <Text size="sm">
                This tracker shows the collective progress of Clara, Emery, and Aiden toward their Bearded Dragon goal.
                Data is updated every 30 seconds to show all kids' contributions.
              </Text>
            </Alert>
          </>
        )}
      </Stack>
    </Container>
  );
};

export default BeardedDragonGoalPage;
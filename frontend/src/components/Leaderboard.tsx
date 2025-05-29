import React, { useState, useEffect } from 'react';
import { Table, Text, LoadingOverlay, Card, ScrollArea, Avatar, Group, Badge, ThemeIcon } from '@mantine/core';
import { useAuth } from '../App';  // Updated import path
import { getLeaderboard } from '../services/api';
import type { User } from '../services/api';  // Using existing User type
import AvatarPreview from './AvatarPreview';

const Leaderboard = () => {
  const [scores, setScores] = useState<User[]>([]);  // Using User type from API
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { currentUser } = useAuth();  // Updated to match AuthContext

  useEffect(() => {
    const fetchScores = async () => {
      try {
        const response = await getLeaderboard();
        setScores(response.data);  // Properly accessing response data
      } catch (err) {
        setError('Failed to load leaderboard');
        console.error('Error fetching leaderboard:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchScores();
  }, []);

  if (loading) return <LoadingOverlay visible />;
  if (error) return <Text c="red">{error}</Text>;  // Using correct Mantine prop

  return (
    <Card shadow="sm" padding="lg" radius="md" withBorder>
      {/* The <Title> is now in LeaderboardPage.tsx, so we can remove it from here if it's redundant */}
      {/* <Text fz="xl" fw={700} mb="md" ta="center">
        Leaderboard
      </Text> */}
      <ScrollArea mah={400}> {/* Max height before scroll */}
        <Table striped highlightOnHover verticalSpacing="sm">
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Rank</Table.Th>
              <Table.Th>Player</Table.Th>
              <Table.Th ta="right">Points</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {scores.length > 0 ? (
              scores.map((user, index) => (
                <Table.Tr key={user.id}>
                  <Table.Td>
                    <Text fw={500}>
                      {index + 1 === 1 ? '🥇' : index + 1 === 2 ? '🥈' : index + 1 === 3 ? '🥉' : index + 1}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Group gap="sm">
                      {user.character ? (
                        <AvatarPreview
                          emoji={user.character.emoji}
                          color={user.character.color}
                          customization={user.character.avatar_customization}
                          size={40}
                        />
                      ) : (
                        <Avatar size="md" radius="xl" />
                      )}
                      <Text fz="sm" fw={500}>
                        {user.username}
                      </Text>
                    </Group>
                  </Table.Td>
                  <Table.Td ta="right">
                    <Badge color="yellow" variant="filled" size="lg">
                      {user.points !== null && user.points !== undefined ? user.points : 'N/A'}
                    </Badge>
                  </Table.Td>
                </Table.Tr>
              ))
            ) : (
              <Table.Tr>
                <Table.Td colSpan={3}>
                  <Text ta="center" c="dimmed" py="md">
                    No scores yet. Be the first!
                  </Text>
                </Table.Td>
              </Table.Tr>
            )}
          </Table.Tbody>
        </Table>
      </ScrollArea>
    </Card>
  );
};

export default Leaderboard;
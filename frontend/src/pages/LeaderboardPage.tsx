import React from 'react';
import { Container, Paper, Title, Space } from '@mantine/core';
import Leaderboard from '../components/Leaderboard'; // Assuming Leaderboard.tsx is in components

const LeaderboardPage = () => {
  return (
    <Container size="md" my="xl">
      <Paper shadow="sm" p="lg" radius="md" withBorder>
        <Title order={1} ta="center" mb="xl">
          Leaderboard
        </Title>
        <Leaderboard />
      </Paper>
      <Space h="xl" />
    </Container>
  );
};

export default LeaderboardPage;
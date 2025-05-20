import React from 'react';
import { Container, Title, Text, Paper, List, ThemeIcon } from '@mantine/core';
import { IconBulb } from '@tabler/icons-react';

const ProjectIdeaPage: React.FC = () => {
  return (
    <Container py="lg">
      <Paper shadow="md" p="xl" radius="md" withBorder>
        <Title order={2} ta="center" mb="xl">
          Project Idea: AI-Powered Personalized Skill Development App
        </Title>

        <Text fw={500} size="lg" mb="sm">Concept:</Text>
        <Text mb="lg">
          An app that uses AI to create highly personalized learning paths for users wanting to acquire new skills (e.g., coding, a new language, playing an instrument, digital marketing). It would adapt to their learning pace, preferred learning style (visual, auditory, kinesthetic), and existing knowledge.
        </Text>

        <Text fw={500} size="lg" mb="sm">Why it could be good:</Text>
        <List
          spacing="xs"
          size="sm"
          center
          mb="lg"
          icon={
            <ThemeIcon color="teal" size={24} radius="xl">
              <IconBulb size="1rem" />
            </ThemeIcon>
          }
        >
          <List.Item>
            <Text fw={500} component="span">Addresses a Need:</Text> Lifelong learning and skill development are increasingly important. Generic online courses often lack personalization.
          </List.Item>
          <List.Item>
            <Text fw={500} component="span">AI Trend:</Text> Leverages the growing power and accessibility of AI for tailored experiences.
          </List.Item>
          <List.Item>
            <Text fw={500} component="span">Market Potential:</Text> Students, professionals looking to upskill or reskill, hobbyists. Monetization could be through premium features, subscriptions, or certifications.
          </List.Item>
          <List.Item>
            <Text fw={500} component="span">Unique Value:</Text> Deep personalization beyond what most current learning platforms offer.
          </List.Item>
        </List>
      </Paper>
    </Container>
  );
};

export default ProjectIdeaPage;
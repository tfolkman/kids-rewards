import React, { useState, useEffect, useRef } from 'react';
import { Button, Group, Text, Paper, Stack, Badge, Progress } from '@mantine/core';
import { IconPlayerPlay, IconPlayerPause, IconPlayerStop, IconFlame } from '@tabler/icons-react';

interface EffortTimerProps {
  onTimeUpdate: (minutes: number) => void;
  isRetry?: boolean;
}

const EffortTimer: React.FC<EffortTimerProps> = ({ onTimeUpdate, isRetry = false }) => {
  const [seconds, setSeconds] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const minutes = Math.floor(seconds / 60);
  const displaySeconds = seconds % 60;
  const effortPoints = Math.min(Math.floor(minutes * 0.5), 10);
  const progressValue = Math.min((effortPoints / 10) * 100, 100);

  useEffect(() => {
    if (isRunning) {
      intervalRef.current = setInterval(() => {
        setSeconds(prev => {
          const newSeconds = prev + 1;
          // Update parent component every minute
          if (newSeconds % 60 === 0) {
            onTimeUpdate(Math.floor(newSeconds / 60));
          }
          return newSeconds;
        });
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRunning, onTimeUpdate]);

  const handleStart = () => {
    setIsRunning(true);
  };

  const handlePause = () => {
    setIsRunning(false);
  };

  const handleStop = () => {
    setIsRunning(false);
    onTimeUpdate(minutes); // Send final time to parent
  };

  const handleReset = () => {
    setIsRunning(false);
    setSeconds(0);
    onTimeUpdate(0);
  };

  const getEncouragementMessage = () => {
    if (minutes < 1) return "Start your timer to track effort!";
    if (minutes < 5) return "Great start! Keep going!";
    if (minutes < 10) return "Awesome effort! You're doing great!";
    if (minutes < 15) return "Amazing persistence! Almost at max points!";
    if (minutes >= 20) return "Maximum effort points earned! You're a star! 🌟";
    return "Keep up the great work!";
  };

  return (
    <Paper p="md" withBorder>
      <Stack gap="sm">
        {isRetry && (
          <Badge color="orange" variant="filled" size="lg">
            <Group gap={4}>
              <IconFlame size={16} />
              <Text size="sm">Keep Trying! Every effort counts!</Text>
            </Group>
          </Badge>
        )}

        <Group justify="space-between">
          <div>
            <Text size="sm" c="dimmed">Time Spent</Text>
            <Text size="xl" fw={700}>
              {String(minutes).padStart(2, '0')}:{String(displaySeconds).padStart(2, '0')}
            </Text>
          </div>
          
          <div>
            <Text size="sm" c="dimmed">Effort Points</Text>
            <Group gap={4}>
              <Text size="xl" fw={700} c="teal">
                +{effortPoints}
              </Text>
              <Text size="xs" c="dimmed">(max 10)</Text>
            </Group>
          </div>
        </Group>

        <Progress 
          value={progressValue} 
          color="teal" 
          size="lg" 
          radius="xl"
          animated={isRunning}
        />

        <Text size="sm" ta="center" c="blue" fw={500}>
          {getEncouragementMessage()}
        </Text>

        <Group justify="center">
          {!isRunning ? (
            <>
              <Button
                leftSection={<IconPlayerPlay size={16} />}
                onClick={handleStart}
                color="green"
                variant="filled"
              >
                {seconds === 0 ? 'Start Timer' : 'Resume'}
              </Button>
              {seconds > 0 && (
                <Button
                  onClick={handleReset}
                  variant="subtle"
                  color="gray"
                >
                  Reset
                </Button>
              )}
            </>
          ) : (
            <>
              <Button
                leftSection={<IconPlayerPause size={16} />}
                onClick={handlePause}
                color="yellow"
                variant="filled"
              >
                Pause
              </Button>
              <Button
                leftSection={<IconPlayerStop size={16} />}
                onClick={handleStop}
                color="red"
                variant="filled"
              >
                Stop & Save
              </Button>
            </>
          )}
        </Group>

        {minutes >= 1 && (
          <Text size="xs" ta="center" c="dimmed">
            Tip: Effort shows character! {minutes >= 10 && "You're earning points even if this chore isn't approved!"}
          </Text>
        )}
      </Stack>
    </Paper>
  );
};

export default EffortTimer;
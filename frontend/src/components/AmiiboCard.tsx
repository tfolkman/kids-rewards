import React from 'react';
import {
    Card,
    Text,
    Badge,
    Button,
    Group,
    Box,
    Center,
    Stack,
    ActionIcon,
    Tooltip,
    useMantineTheme,
    rem,
} from '@mantine/core';
import {
    IconEdit,
    IconTrash,
    IconLock,
    IconLockOpen,
    IconSparkles,
    IconStar,
} from '@tabler/icons-react';
import AvatarPreview from './AvatarPreview';
import { Character } from '../services/api';

interface AmiiboCardProps {
    character: Character;
    isSelected: boolean;
    isLocked: boolean;
    userPoints: number;
    isParent: boolean;
    onSelect: (character: Character) => void;
    onEdit?: (character: Character) => void;
    onDelete?: (characterId: string) => void;
}

const AmiiboCard: React.FC<AmiiboCardProps> = ({
    character,
    isSelected,
    isLocked,
    userPoints,
    isParent,
    onSelect,
    onEdit,
    onDelete,
}) => {
    const theme = useMantineTheme();

    const baseGradient = isSelected
        ? 'linear-gradient(135deg, #4fc3f7 0%, #29b6f6 25%, #03a9f4 50%, #0288d1 75%, #0277bd 100%)'
        : isLocked
        ? 'linear-gradient(135deg, #757575 0%, #616161 25%, #424242 50%, #303030 75%, #212121 100%)'
        : 'linear-gradient(135deg, #81c784 0%, #66bb6a 25%, #4caf50 50%, #43a047 75%, #388e3c 100%)';

    const cardStyle = {
        background: isSelected
            ? 'linear-gradient(145deg, #e3f2fd 0%, #bbdefb 50%, #90caf9 100%)'
            : isLocked
            ? 'linear-gradient(145deg, #fafafa 0%, #f5f5f5 50%, #eeeeee 100%)'
            : 'linear-gradient(145deg, #f1f8e9 0%, #dcedc8 50%, #c5e1a5 100%)',
        border: isSelected
            ? '3px solid #2196f3'
            : isLocked
            ? '3px solid #9e9e9e'
            : '3px solid #4caf50',
        borderRadius: rem(20),
        overflow: 'hidden',
        position: 'relative' as const,
        transform: isSelected ? 'scale(1.05)' : 'scale(1)',
        transition: 'all 0.3s ease',
        cursor: 'pointer',
        boxShadow: isSelected
            ? '0 8px 32px rgba(33, 150, 243, 0.3)'
            : isLocked
            ? '0 4px 16px rgba(0, 0, 0, 0.2)'
            : '0 4px 16px rgba(76, 175, 80, 0.3)',
    };

    const sparkleStyle = {
        position: 'absolute' as const,
        top: rem(8),
        right: rem(8),
        color: isSelected ? '#ff9800' : '#ffc107',
        filter: 'drop-shadow(0 0 4px rgba(255, 193, 7, 0.6))',
    };

    return (
        <Card
            style={cardStyle}
            p="lg"
            onClick={() => !isLocked && onSelect(character)}
        >
            {/* Sparkle effect for selected character */}
            {isSelected && (
                <Box style={sparkleStyle}>
                    <IconStar size={24} fill="currentColor" />
                </Box>
            )}

            {/* Parent controls */}
            {isParent && (
                <Group justify="flex-end" gap={4} style={{ position: 'absolute', top: rem(8), left: rem(8), zIndex: 2 }}>
                    <Tooltip label="Edit Character">
                        <ActionIcon
                            variant="filled"
                            color="blue"
                            size="sm"
                            onClick={(e) => {
                                e.stopPropagation();
                                onEdit?.(character);
                            }}
                        >
                            <IconEdit size={14} />
                        </ActionIcon>
                    </Tooltip>
                    <Tooltip label="Delete Character">
                        <ActionIcon
                            variant="filled"
                            color="red"
                            size="sm"
                            onClick={(e) => {
                                e.stopPropagation();
                                onDelete?.(character.id);
                            }}
                        >
                            <IconTrash size={14} />
                        </ActionIcon>
                    </Tooltip>
                </Group>
            )}

            <Stack gap="md" align="center">
                {/* Character Name */}
                <Text
                    fw={700}
                    size="lg"
                    ta="center"
                    c={isLocked ? 'dimmed' : 'dark'}
                    style={{
                        textShadow: isSelected ? '0 1px 2px rgba(0,0,0,0.1)' : 'none',
                        marginTop: isParent ? rem(24) : 0,
                    }}
                >
                    {character.name}
                </Text>

                {/* Amiibo-style character display */}
                <Box style={{ position: 'relative' }}>
                    {/* Character base/platform */}
                    <Box
                        style={{
                            width: rem(160),
                            height: rem(40),
                            background: baseGradient,
                            borderRadius: rem(80),
                            boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                            position: 'relative',
                            border: `2px solid ${isSelected ? '#1976d2' : isLocked ? '#616161' : '#2e7d32'}`,
                        }}
                    >
                        {/* Base reflection */}
                        <Box
                            style={{
                                position: 'absolute',
                                top: rem(4),
                                left: rem(20),
                                right: rem(20),
                                height: rem(8),
                                background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%)',
                                borderRadius: rem(4),
                            }}
                        />
                        
                        {/* Character standing on base */}
                        <Center style={{ position: 'absolute', top: rem(-60), left: '50%', transform: 'translateX(-50%)' }}>
                            <AvatarPreview
                                emoji={character.emoji}
                                color={character.color}
                                customization={character.avatar_customization}
                                size={120}
                            />
                        </Center>
                    </Box>
                </Box>

                {/* Character description */}
                {character.description && (
                    <Text
                        size="sm"
                        ta="center"
                        c="dimmed"
                        style={{
                            maxWidth: rem(140),
                            lineHeight: 1.3,
                        }}
                    >
                        {character.description}
                    </Text>
                )}

                {/* Points requirement and status */}
                <Group justify="center" gap="xs">
                    <Badge
                        size="lg"
                        color={isLocked ? 'gray' : isSelected ? 'blue' : 'green'}
                        variant={isSelected ? 'filled' : 'light'}
                        leftSection={isLocked ? <IconLock size={14} /> : <IconLockOpen size={14} />}
                        style={{
                            textShadow: isSelected ? '0 1px 2px rgba(0,0,0,0.1)' : 'none',
                        }}
                    >
                        {character.unlocked_at_points} Points
                    </Badge>
                    
                    {isSelected && (
                        <Badge
                            size="lg"
                            color="yellow"
                            variant="filled"
                            leftSection={<IconSparkles size={14} />}
                        >
                            Active
                        </Badge>
                    )}
                </Group>

                {/* Action button */}
                <Button
                    fullWidth
                    size="md"
                    variant={isSelected ? 'light' : 'filled'}
                    color={isSelected ? 'blue' : 'green'}
                    disabled={isLocked}
                    leftSection={<IconSparkles size={16} />}
                    style={{
                        borderRadius: rem(12),
                        fontWeight: 600,
                        textTransform: 'uppercase',
                        letterSpacing: rem(0.5),
                        boxShadow: isLocked ? 'none' : '0 2px 8px rgba(0,0,0,0.15)',
                    }}
                >
                    {isSelected ? 'Customize' : isLocked ? 'Locked' : 'Select'}
                </Button>

                {/* Points progress for locked characters */}
                {isLocked && !isParent && (
                    <Box style={{ width: '100%' }}>
                        <Group justify="space-between" mb={4}>
                            <Text size="xs" c="dimmed">Progress</Text>
                            <Text size="xs" c="dimmed">
                                {userPoints}/{character.unlocked_at_points}
                            </Text>
                        </Group>
                        <Box
                            style={{
                                width: '100%',
                                height: rem(6),
                                background: theme.colors.gray[3],
                                borderRadius: rem(3),
                                overflow: 'hidden',
                            }}
                        >
                            <Box
                                style={{
                                    width: `${Math.min((userPoints / character.unlocked_at_points) * 100, 100)}%`,
                                    height: '100%',
                                    background: 'linear-gradient(90deg, #4caf50, #66bb6a)',
                                    transition: 'width 0.3s ease',
                                }}
                            />
                        </Box>
                    </Box>
                )}
            </Stack>
        </Card>
    );
};

export default AmiiboCard;
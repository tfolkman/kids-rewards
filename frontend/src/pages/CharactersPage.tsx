import React, { useState, useEffect } from 'react';
import {
    Container,
    Title,
    SimpleGrid,
    Card,
    Text,
    Badge,
    Button,
    Group,
    Modal,
    TextInput,
    ColorInput,
    Textarea,
    NumberInput,
    Stack,
    Center,
    LoadingOverlay,
    Alert,
    Box,
    ActionIcon,
    rem,
    Paper,
    ThemeIcon,
    useMantineTheme,
    Select,
    Tabs,
    Divider,
    BackgroundImage,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { 
    IconPlus, 
    IconEdit, 
    IconTrash, 
    IconAlertCircle,
    IconCheck,
    IconLock,
    IconLockOpen,
    IconSparkles,
    IconPalette,
    IconShirt,
    IconMasksTheater,
    IconDeviceGamepad2,
    IconStar,
} from '@tabler/icons-react';
import * as api from '../services/api';
import { useAuth } from '../App';
import AvatarPreview from '../components/AvatarPreview';
import AmiiboCard from '../components/AmiiboCard';

const CharactersPage = () => {
    const { currentUser } = useAuth();
    const theme = useMantineTheme();
    const [characters, setCharacters] = useState<api.Character[]>([]);
    const [availableCharacters, setAvailableCharacters] = useState<api.Character[]>([]);
    const [myCharacter, setMyCharacter] = useState<api.Character | null>(null);
    const [loading, setLoading] = useState(true);
    const [modalOpened, { open: openModal, close: closeModal }] = useDisclosure(false);
    const [customizeModalOpened, { open: openCustomizeModal, close: closeCustomizeModal }] = useDisclosure(false);
    const [editingCharacter, setEditingCharacter] = useState<api.Character | null>(null);
    const [selectedCharacterForCustomization, setSelectedCharacterForCustomization] = useState<api.Character | null>(null);
    
    // Form state
    const [formData, setFormData] = useState({
        name: '',
        emoji: '',
        color: '#000000',
        description: '',
        unlocked_at_points: 0
    });

    // Customization state
    const [customization, setCustomization] = useState<api.AvatarCustomization>({
        hat: undefined,
        hat_color: '#000000',
        accessory: undefined,
        accessory_color: '#000000',
        hair_style: undefined,
        hair_color: '#000000',
        outfit: undefined,
        outfit_color: '#000000',
        background: 'plain',
        background_color: undefined,
    });

    const isParent = currentUser?.role === 'parent';
    const userPoints = currentUser?.points ?? 0;

    // Customization options
    const hatOptions = [
        { value: '', label: 'None' },
        { value: 'cap', label: '🧢 Baseball Cap' },
        { value: 'beanie', label: '🎩 Top Hat' },
        { value: 'wizard', label: '🧙 Wizard Hat' },
        { value: 'crown', label: '👑 Crown' },
        { value: 'cowboy', label: '🤠 Cowboy Hat' },
        { value: 'party', label: '🥳 Party Hat' },
        { value: 'santa', label: '🎅 Santa Hat' },
    ];

    const accessoryOptions = [
        { value: '', label: 'None' },
        { value: 'glasses', label: '👓 Glasses' },
        { value: 'sunglasses', label: '🕶️ Sunglasses' },
        { value: 'monocle', label: '🧐 Monocle' },
        { value: 'eyepatch', label: '🏴‍☠️ Eye Patch' },
    ];

    const outfitOptions = [
        { value: '', label: 'None' },
        { value: 'casual', label: '👕 Casual' },
        { value: 'formal', label: '👔 Formal' },
        { value: 'superhero', label: '🦸 Superhero' },
        { value: 'ninja', label: '🥷 Ninja' },
        { value: 'doctor', label: '👨‍⚕️ Doctor' },
        { value: 'chef', label: '👨‍🍳 Chef' },
        { value: 'astronaut', label: '👨‍🚀 Astronaut' },
    ];

    const backgroundOptions = [
        { value: 'plain', label: 'Plain' },
        { value: 'stars', label: '✨ Stars' },
        { value: 'clouds', label: '☁️ Clouds' },
        { value: 'rainbow', label: '🌈 Rainbow' },
    ];

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [allCharsResponse, myCharResponse] = await Promise.all([
                isParent ? api.getAllCharacters() : api.getAvailableCharacters(),
                api.getMyCharacter()
            ]);
            
            if (isParent) {
                setCharacters(allCharsResponse.data);
            } else {
                setAvailableCharacters(allCharsResponse.data);
            }
            
            setMyCharacter(myCharResponse.data);
        } catch (error) {
            notifications.show({
                title: 'Error',
                message: 'Failed to load characters',
                color: 'red',
            });
        } finally {
            setLoading(false);
        }
    };

    const handleCreateOrUpdate = async () => {
        try {
            if (editingCharacter) {
                await api.updateCharacter(editingCharacter.id, formData);
                notifications.show({
                    title: 'Success',
                    message: 'Character updated successfully',
                    color: 'green',
                });
            } else {
                await api.createCharacter(formData);
                notifications.show({
                    title: 'Success',
                    message: 'Character created successfully',
                    color: 'green',
                });
            }
            closeModal();
            resetForm();
            loadData();
        } catch (error) {
            notifications.show({
                title: 'Error',
                message: 'Failed to save character',
                color: 'red',
            });
        }
    };

    const handleDelete = async (characterId: string) => {
        try {
            await api.deleteCharacter(characterId);
            notifications.show({
                title: 'Success',
                message: 'Character deleted successfully',
                color: 'green',
            });
            loadData();
        } catch (error) {
            notifications.show({
                title: 'Error',
                message: 'Failed to delete character',
                color: 'red',
            });
        }
    };

    const handleSelectCharacter = async (character: api.Character) => {
        if (!isParent && userPoints < character.unlocked_at_points) {
            notifications.show({
                title: 'Not enough points',
                message: `You need ${character.unlocked_at_points} points to unlock this character`,
                color: 'orange',
            });
            return;
        }

        setSelectedCharacterForCustomization(character);
        setCustomization({
            hat: undefined,
            hat_color: '#000000',
            accessory: undefined,
            accessory_color: '#000000',
            hair_style: undefined,
            hair_color: '#000000',
            outfit: undefined,
            outfit_color: '#000000',
            background: 'plain',
            background_color: character.color,
        });
        openCustomizeModal();
    };

    const handleSaveCustomization = async () => {
        if (!selectedCharacterForCustomization) return;

        try {
            await api.setMyCharacter(selectedCharacterForCustomization.id, customization);
            notifications.show({
                title: 'Success',
                message: 'Character selected and customized!',
                color: 'green',
            });
            closeCustomizeModal();
            loadData();
        } catch (error) {
            notifications.show({
                title: 'Error',
                message: 'Failed to set character',
                color: 'red',
            });
        }
    };

    const resetForm = () => {
        setFormData({
            name: '',
            emoji: '',
            color: '#000000',
            description: '',
            unlocked_at_points: 0
        });
        setEditingCharacter(null);
    };

    const openEditModal = (character: api.Character) => {
        setEditingCharacter(character);
        setFormData({
            name: character.name,
            emoji: character.emoji,
            color: character.color,
            description: character.description || '',
            unlocked_at_points: character.unlocked_at_points
        });
        openModal();
    };

    if (loading) {
        return (
            <Center style={{ height: '50vh' }}>
                <LoadingOverlay visible={true} />
            </Center>
        );
    }

    const displayCharacters = isParent ? characters : availableCharacters;

    return (
        <>
            <Box
            style={{
                minHeight: '100vh',
                background: 'linear-gradient(135deg, #e3f2fd 0%, #bbdefb 20%, #90caf9 40%, #64b5f6 60%, #42a5f5 80%, #2196f3 100%)',
                position: 'relative',
            }}
        >
            {/* Nintendo-style background pattern */}
            <Box
                style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: `
                        radial-gradient(circle at 20% 20%, rgba(255,255,255,0.1) 0%, transparent 50%),
                        radial-gradient(circle at 80% 80%, rgba(255,255,255,0.1) 0%, transparent 50%),
                        radial-gradient(circle at 40% 60%, rgba(255,255,255,0.05) 0%, transparent 50%)
                    `,
                    pointerEvents: 'none',
                }}
            />

            <Container size="xl" style={{ position: 'relative', zIndex: 1 }}>
                {/* Header */}
                <Paper
                    p="xl"
                    mb="xl"
                    style={{
                        background: 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
                        borderRadius: rem(20),
                        border: '3px solid #2196f3',
                        boxShadow: '0 8px 32px rgba(33, 150, 243, 0.3)',
                    }}
                >
                    <Group justify="space-between" align="center">
                        <Group>
                            <IconDeviceGamepad2 size={32} color="#2196f3" />
                            <Box>
                                <Title
                                    order={1}
                                    style={{
                                        background: 'linear-gradient(45deg, #2196f3, #1976d2)',
                                        backgroundClip: 'text',
                                        WebkitBackgroundClip: 'text',
                                        WebkitTextFillColor: 'transparent',
                                        fontSize: rem(32),
                                        fontWeight: 800,
                                        textShadow: '2px 2px 4px rgba(0,0,0,0.1)',
                                    }}
                                >
                                    Character Collection
                                </Title>
                                <Text size="lg" c="dimmed">
                                    Select and customize your character
                                </Text>
                            </Box>
                        </Group>
                        {isParent && (
                            <Button
                                size="lg"
                                leftSection={<IconPlus size={20} />}
                                onClick={openModal}
                                style={{
                                    background: 'linear-gradient(45deg, #4caf50, #388e3c)',
                                    borderRadius: rem(12),
                                    fontWeight: 600,
                                    textTransform: 'uppercase',
                                    letterSpacing: rem(1),
                                }}
                            >
                                Create Character
                            </Button>
                        )}
                    </Group>
                </Paper>

                {/* Current Character Showcase */}
                {myCharacter && (
                    <Paper
                        p="xl"
                        mb="xl"
                        style={{
                            background: 'linear-gradient(145deg, #fff3e0 0%, #ffe0b2 50%, #ffcc02 100%)',
                            borderRadius: rem(20),
                            border: '3px solid #ff9800',
                            boxShadow: '0 8px 32px rgba(255, 152, 0, 0.3)',
                            position: 'relative',
                            overflow: 'hidden',
                        }}
                    >
                        {/* Sparkle decorations */}
                        <IconStar
                            size={24}
                            style={{
                                position: 'absolute',
                                top: rem(16),
                                right: rem(16),
                                color: '#ff9800',
                                filter: 'drop-shadow(0 0 4px rgba(255, 152, 0, 0.6))',
                            }}
                            fill="currentColor"
                        />
                        <IconStar
                            size={16}
                            style={{
                                position: 'absolute',
                                top: rem(32),
                                right: rem(48),
                                color: '#ffc107',
                                filter: 'drop-shadow(0 0 4px rgba(255, 193, 7, 0.6))',
                            }}
                            fill="currentColor"
                        />

                        <Group align="center">
                            <Box style={{ position: 'relative' }}>
                                {/* Enhanced character display */}
                                <Box
                                    style={{
                                        width: rem(120),
                                        height: rem(30),
                                        background: 'linear-gradient(135deg, #ff9800 0%, #f57c00 100%)',
                                        borderRadius: rem(60),
                                        boxShadow: '0 4px 16px rgba(245, 124, 0, 0.4)',
                                        position: 'relative',
                                        border: '2px solid #e65100',
                                    }}
                                >
                                    <Box
                                        style={{
                                            position: 'absolute',
                                            top: rem(3),
                                            left: rem(15),
                                            right: rem(15),
                                            height: rem(6),
                                            background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.4) 50%, transparent 100%)',
                                            borderRadius: rem(3),
                                        }}
                                    />
                                    
                                    <Center style={{ position: 'absolute', top: rem(-45), left: '50%', transform: 'translateX(-50%)' }}>
                                        <AvatarPreview
                                            emoji={myCharacter.emoji}
                                            color={myCharacter.color}
                                            customization={myCharacter.avatar_customization}
                                            size={100}
                                        />
                                    </Center>
                                </Box>
                            </Box>
                            
                            <Box style={{ flex: 1 }}>
                                <Group>
                                    <IconStar size={20} color="#ff9800" fill="currentColor" />
                                    <Text
                                        fw={700}
                                        size="xl"
                                        style={{
                                            color: '#e65100',
                                            textShadow: '1px 1px 2px rgba(0,0,0,0.1)',
                                        }}
                                    >
                                        Active Character
                                    </Text>
                                </Group>
                                <Text size="lg" fw={600} c="dark" mb={4}>
                                    {myCharacter.name}
                                </Text>
                                <Text size="md" c="dimmed">
                                    {myCharacter.description || 'Your selected character'}
                                </Text>
                            </Box>
                            
                            <Button
                                size="lg"
                                variant="filled"
                                color="orange"
                                onClick={() => handleSelectCharacter(myCharacter)}
                                leftSection={<IconSparkles size={18} />}
                                style={{
                                    borderRadius: rem(12),
                                    fontWeight: 600,
                                    textTransform: 'uppercase',
                                    letterSpacing: rem(0.5),
                                }}
                            >
                                Customize
                            </Button>
                        </Group>
                    </Paper>
                )}

                {/* Character Grid */}
                <SimpleGrid 
                    cols={{ base: 1, sm: 2, md: 3, lg: 4, xl: 5 }} 
                    spacing="xl"
                    style={{ marginBottom: rem(40) }}
                >
                    {displayCharacters.map((character) => {
                        const isLocked = !isParent && userPoints < character.unlocked_at_points;
                        const isSelected = myCharacter?.id === character.id;

                        return (
                            <AmiiboCard
                                key={character.id}
                                character={character}
                                isSelected={isSelected}
                                isLocked={isLocked}
                                userPoints={userPoints}
                                isParent={isParent}
                                onSelect={handleSelectCharacter}
                                onEdit={openEditModal}
                                onDelete={handleDelete}
                            />
                        );
                    })}
                </SimpleGrid>
            </Container>
        </Box>

            {/* Create/Edit Modal */}
            <Modal
                opened={modalOpened}
                onClose={() => { closeModal(); resetForm(); }}
                title={
                    <Group>
                        <IconDeviceGamepad2 size={24} color="#2196f3" />
                        <Text fw={700} size="lg" style={{ color: '#2196f3' }}>
                            {editingCharacter ? 'Edit Character' : 'Create New Character'}
                        </Text>
                    </Group>
                }
                size="md"
                styles={{
                    content: {
                        background: 'linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%)',
                        border: '2px solid #2196f3',
                        borderRadius: rem(16),
                    },
                    header: {
                        background: 'linear-gradient(90deg, #e3f2fd 0%, #bbdefb 100%)',
                        borderRadius: `${rem(14)} ${rem(14)} 0 0`,
                        borderBottom: '2px solid #2196f3',
                    }
                }}
            >
                <Stack gap="lg">
                    <TextInput
                        label="Name"
                        placeholder="Character name"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.currentTarget.value })}
                        required
                        styles={{
                            input: { borderRadius: rem(8), borderColor: '#90caf9' },
                            label: { fontWeight: 600, color: '#1976d2' }
                        }}
                    />
                    
                    <TextInput
                        label="Emoji"
                        placeholder="🦁"
                        value={formData.emoji}
                        onChange={(e) => setFormData({ ...formData, emoji: e.currentTarget.value })}
                        required
                        styles={{
                            input: { borderRadius: rem(8), borderColor: '#90caf9' },
                            label: { fontWeight: 600, color: '#1976d2' }
                        }}
                    />
                    
                    <ColorInput
                        label="Theme Color"
                        placeholder="Pick color"
                        value={formData.color}
                        onChange={(value) => setFormData({ ...formData, color: value })}
                        required
                        styles={{
                            input: { borderRadius: rem(8), borderColor: '#90caf9' },
                            label: { fontWeight: 600, color: '#1976d2' }
                        }}
                    />
                    
                    <Textarea
                        label="Description"
                        placeholder="Character description (optional)"
                        value={formData.description}
                        onChange={(e) => setFormData({ ...formData, description: e.currentTarget.value })}
                        autosize
                        minRows={2}
                        maxRows={4}
                        styles={{
                            input: { borderRadius: rem(8), borderColor: '#90caf9' },
                            label: { fontWeight: 600, color: '#1976d2' }
                        }}
                    />
                    
                    <NumberInput
                        label="Points Required to Unlock"
                        placeholder="0"
                        value={formData.unlocked_at_points}
                        onChange={(value) => setFormData({ ...formData, unlocked_at_points: typeof value === 'number' ? value : 0 })}
                        min={0}
                        required
                        styles={{
                            input: { borderRadius: rem(8), borderColor: '#90caf9' },
                            label: { fontWeight: 600, color: '#1976d2' }
                        }}
                    />
                    
                    <Group justify="flex-end" mt="md">
                        <Button 
                            variant="outline" 
                            onClick={closeModal}
                            style={{
                                borderRadius: rem(8),
                                borderColor: '#90caf9',
                                color: '#1976d2',
                            }}
                        >
                            Cancel
                        </Button>
                        <Button 
                            onClick={handleCreateOrUpdate}
                            style={{
                                background: 'linear-gradient(45deg, #2196f3, #1976d2)',
                                borderRadius: rem(8),
                                fontWeight: 600,
                            }}
                        >
                            {editingCharacter ? 'Update' : 'Create'}
                        </Button>
                    </Group>
                </Stack>
            </Modal>

            {/* Customization Modal */}
            <Modal
                opened={customizeModalOpened}
                onClose={closeCustomizeModal}
                title={
                    <Group>
                        <IconSparkles size={24} color="#ff9800" />
                        <Text fw={700} size="lg" style={{ color: '#ff9800' }}>
                            Customize Your Character
                        </Text>
                    </Group>
                }
                size="lg"
                styles={{
                    content: {
                        background: 'linear-gradient(145deg, #fff8e1 0%, #ffecb3 100%)',
                        border: '2px solid #ff9800',
                        borderRadius: rem(16),
                    },
                    header: {
                        background: 'linear-gradient(90deg, #fff3e0 0%, #ffe0b2 100%)',
                        borderRadius: `${rem(14)} ${rem(14)} 0 0`,
                        borderBottom: '2px solid #ff9800',
                    }
                }}
            >
                <Stack gap="lg">
                    <Center>
                        <Box style={{ position: 'relative' }}>
                            {/* Character base/platform for preview */}
                            <Box
                                style={{
                                    width: rem(240),
                                    height: rem(50),
                                    background: 'linear-gradient(135deg, #ff9800 0%, #f57c00 100%)',
                                    borderRadius: rem(120),
                                    boxShadow: '0 6px 20px rgba(245, 124, 0, 0.4)',
                                    position: 'relative',
                                    border: '3px solid #e65100',
                                }}
                            >
                                <Box
                                    style={{
                                        position: 'absolute',
                                        top: rem(6),
                                        left: rem(30),
                                        right: rem(30),
                                        height: rem(10),
                                        background: 'linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.4) 50%, transparent 100%)',
                                        borderRadius: rem(5),
                                    }}
                                />
                                
                                <Center style={{ position: 'absolute', top: rem(-90), left: '50%', transform: 'translateX(-50%)' }}>
                                    <AvatarPreview
                                        emoji={selectedCharacterForCustomization?.emoji || ''}
                                        color={selectedCharacterForCustomization?.color || '#000000'}
                                        customization={customization}
                                        size={180}
                                    />
                                </Center>
                            </Box>
                        </Box>
                    </Center>

                    <Divider color="#ff9800" size="sm" />

                    <Tabs 
                        defaultValue="appearance"
                        styles={{
                            tab: {
                                borderRadius: rem(8),
                                fontWeight: 600,
                                '&[data-active]': {
                                    background: 'linear-gradient(45deg, #ff9800, #f57c00)',
                                    color: 'white',
                                    borderColor: '#ff9800',
                                }
                            }
                        }}
                    >
                        <Tabs.List>
                            <Tabs.Tab value="appearance" leftSection={<IconPalette size={16} />}>
                                Appearance
                            </Tabs.Tab>
                            <Tabs.Tab value="accessories" leftSection={<IconMasksTheater size={16} />}>
                                Accessories
                            </Tabs.Tab>
                            <Tabs.Tab value="outfit" leftSection={<IconShirt size={16} />}>
                                Outfit
                            </Tabs.Tab>
                        </Tabs.List>

                        <Tabs.Panel value="appearance" pt="xl">
                            <Stack gap="lg">
                                <Select
                                    label="Background Style"
                                    data={backgroundOptions}
                                    value={customization.background}
                                    onChange={(value) => setCustomization({ ...customization, background: value || 'plain' })}
                                    styles={{
                                        input: { borderRadius: rem(8), borderColor: '#ffb74d' },
                                        label: { fontWeight: 600, color: '#f57c00' }
                                    }}
                                />
                                <ColorInput
                                    label="Background Color"
                                    value={customization.background_color || selectedCharacterForCustomization?.color || '#000000'}
                                    onChange={(value) => setCustomization({ ...customization, background_color: value })}
                                    styles={{
                                        input: { borderRadius: rem(8), borderColor: '#ffb74d' },
                                        label: { fontWeight: 600, color: '#f57c00' }
                                    }}
                                />
                            </Stack>
                        </Tabs.Panel>

                        <Tabs.Panel value="accessories" pt="xl">
                            <Stack gap="lg">
                                <Select
                                    label="Hat"
                                    data={hatOptions}
                                    value={customization.hat || ''}
                                    onChange={(value) => setCustomization({ ...customization, hat: value || undefined })}
                                    clearable
                                    styles={{
                                        input: { borderRadius: rem(8), borderColor: '#ffb74d' },
                                        label: { fontWeight: 600, color: '#f57c00' }
                                    }}
                                />
                                {customization.hat && (
                                    <ColorInput
                                        label="Hat Color"
                                        value={customization.hat_color || '#000000'}
                                        onChange={(value) => setCustomization({ ...customization, hat_color: value })}
                                        styles={{
                                            input: { borderRadius: rem(8), borderColor: '#ffb74d' },
                                            label: { fontWeight: 600, color: '#f57c00' }
                                        }}
                                    />
                                )}
                                
                                <Select
                                    label="Accessory"
                                    data={accessoryOptions}
                                    value={customization.accessory || ''}
                                    onChange={(value) => setCustomization({ ...customization, accessory: value || undefined })}
                                    clearable
                                    styles={{
                                        input: { borderRadius: rem(8), borderColor: '#ffb74d' },
                                        label: { fontWeight: 600, color: '#f57c00' }
                                    }}
                                />
                                {customization.accessory && (
                                    <ColorInput
                                        label="Accessory Color"
                                        value={customization.accessory_color || '#000000'}
                                        onChange={(value) => setCustomization({ ...customization, accessory_color: value })}
                                        styles={{
                                            input: { borderRadius: rem(8), borderColor: '#ffb74d' },
                                            label: { fontWeight: 600, color: '#f57c00' }
                                        }}
                                    />
                                )}
                            </Stack>
                        </Tabs.Panel>

                        <Tabs.Panel value="outfit" pt="xl">
                            <Stack gap="lg">
                                <Select
                                    label="Outfit"
                                    data={outfitOptions}
                                    value={customization.outfit || ''}
                                    onChange={(value) => setCustomization({ ...customization, outfit: value || undefined })}
                                    clearable
                                    styles={{
                                        input: { borderRadius: rem(8), borderColor: '#ffb74d' },
                                        label: { fontWeight: 600, color: '#f57c00' }
                                    }}
                                />
                                {customization.outfit && (
                                    <ColorInput
                                        label="Outfit Color"
                                        value={customization.outfit_color || '#000000'}
                                        onChange={(value) => setCustomization({ ...customization, outfit_color: value })}
                                        styles={{
                                            input: { borderRadius: rem(8), borderColor: '#ffb74d' },
                                            label: { fontWeight: 600, color: '#f57c00' }
                                        }}
                                    />
                                )}
                            </Stack>
                        </Tabs.Panel>
                    </Tabs>

                    <Divider color="#ff9800" size="sm" />

                    <Group justify="flex-end" mt="md">
                        <Button 
                            variant="outline" 
                            onClick={closeCustomizeModal}
                            style={{
                                borderRadius: rem(8),
                                borderColor: '#ffb74d',
                                color: '#f57c00',
                            }}
                        >
                            Cancel
                        </Button>
                        <Button 
                            onClick={handleSaveCustomization}
                            leftSection={<IconSparkles size={16} />}
                            style={{
                                background: 'linear-gradient(45deg, #ff9800, #f57c00)',
                                borderRadius: rem(8),
                                fontWeight: 600,
                                textTransform: 'uppercase',
                                letterSpacing: rem(0.5),
                            }}
                        >
                            Save Customization
                        </Button>
                    </Group>
                </Stack>
            </Modal>
        </>
    );
};

export default CharactersPage;
import React, { useState, useEffect, createContext, useContext } from 'react';
import { 
    BrowserRouter as Router,
    Routes, // v6
    Route,  // v6
    Link as RouterLink,
    Navigate, // v6
    Outlet,   // v6
    useNavigate, // v6
    useLocation
} from 'react-router-dom';
import {
    MantineProvider,
    createTheme,
    AppShell,
    Burger,
    Group,
    NavLink,
    Paper,
    TextInput,
    PasswordInput,
    Button,
    Title,
    Text,
    Stack,
    Container,
    Alert,
    Center,
    Divider,
    Box,
    SimpleGrid,
    Card,
    Badge,
    useMantineTheme,
    LoadingOverlay,
    MantineTheme,
    Modal,
    Textarea,
    Menu,
    ActionIcon,
    Avatar,
    rem
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { Notifications, notifications } from '@mantine/notifications';
import { 
    IconAlertCircle, IconLogin, IconUserPlus, IconHome, IconShoppingCart, 
    IconLogout, IconSettings, IconAward, IconUserUp, IconListNumbers, 
    IconReceipt, IconHourglassHigh, IconClipboardList, IconHistory, 
    IconChecklist, IconMessagePlus, IconListCheck, IconMessageChatbot,
    IconUserCheck, IconUser, IconChevronDown, IconTarget
} from '@tabler/icons-react';
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import './App.css';
import './animations.css';
import * as api from './services/api';
import ManageStoreItems from './components/ManageStoreItems';
import AwardPoints from './components/AwardPoints';
import UserManagement from './components/UserManagement';
import SearchBar from './components/SearchBar';
import LeaderboardPage from './pages/LeaderboardPage';
import PurchaseHistoryPage from './pages/PurchaseHistoryPage';
import PendingRequestsPage from './pages/PendingRequestsPage';
import ManageChoresPage from './pages/ManageChoresPage';
import ChoresPage from './pages/ChoresPage';
import ChoreHistoryPage from './pages/ChoreHistoryPage';
import MakeRequestPage from './pages/MakeRequestPage';
import ManageRequestsPage from './pages/ManageRequestsPage';
import MyAssignedChoresPage from './pages/MyAssignedChoresPage';
import AssignChoresPage from './pages/AssignChoresPage';
import BeardedDragonGoalPage from './pages/BeardedDragonGoalPage';
import { StreakDisplay } from './components/StreakDisplay';

interface AuthContextType {
  currentUser: api.User | null | undefined;
  setCurrentUser: React.Dispatch<React.SetStateAction<api.User | null | undefined>>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

const LoginPage = () => {
    const navigate = useNavigate();
    const { setCurrentUser } = useAuth();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            const response = await api.login(username, password);
            localStorage.setItem('token', response.data.access_token);
            const userResponse = await api.getCurrentUser();
            setCurrentUser(userResponse.data);
            navigate('/');
        } catch (err) {
            setError('Failed to login. Check credentials.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container size="xs" style={{ marginTop: '50px' }} className="fade-in">
            <Paper withBorder shadow="md" p={30} mt={30} radius="md" className="card-hover">
                <Title ta="center" order={2} mb="lg">Welcome Back!</Title>
                <form onSubmit={handleSubmit}>
                    <Stack>
                        <TextInput required label="Username" placeholder="Your username" value={username} onChange={(event) => setUsername(event.currentTarget.value)} />
                        <PasswordInput required label="Password" placeholder="Your password" value={password} onChange={(event) => setPassword(event.currentTarget.value)} />
                        {error && <Alert icon={<IconAlertCircle size="1rem" />} title="Login Error" color="red" radius="md">{error}</Alert>}
                        <Button type="submit" fullWidth mt="xl" loading={loading} leftSection={<IconLogin size={16} />}>Login</Button>
                    </Stack>
                </form>
                <Text ta="center" mt="md">Don't have an account? <RouterLink to="/signup" style={{ textDecoration: 'none' }}><Text component="span" c="indigo" fw={500}>Sign Up</Text></RouterLink></Text>
            </Paper>
        </Container>
    );
};

const SignupPage = () => {
    const navigate = useNavigate();
    const { setCurrentUser } = useAuth();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            await api.signup({ username, password });
            const tokenResponse = await api.login(username, password);
            localStorage.setItem('token', tokenResponse.data.access_token);
            const userResponse = await api.getCurrentUser();
            setCurrentUser(userResponse.data);
            navigate('/');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to sign up.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container size="xs" style={{ marginTop: '50px' }} className="fade-in">
            <Paper withBorder shadow="md" p={30} mt={30} radius="md" className="card-hover">
                <Title ta="center" order={2} mb="lg">Create Your Account</Title>
                <form onSubmit={handleSubmit}>
                    <Stack>
                        <TextInput required label="Username" placeholder="Choose a username" value={username} onChange={(event) => setUsername(event.currentTarget.value)} />
                        <PasswordInput required label="Password" placeholder="Choose a password" value={password} onChange={(event) => setPassword(event.currentTarget.value)} />
                        {error && <Alert icon={<IconAlertCircle size="1rem" />} title="Signup Error" color="red" radius="md">{error}</Alert>}
                        <Button type="submit" fullWidth mt="xl" loading={loading} leftSection={<IconUserPlus size={16}/>}>Sign Up</Button>
                    </Stack>
                </form>
                <Text ta="center" mt="md">Already have an account? <RouterLink to="/login" style={{ textDecoration: 'none' }}><Text component="span" c="indigo" fw={500}>Login</Text></RouterLink></Text>
            </Paper>
        </Container>
    );
};

const Dashboard = () => {
    const { currentUser } = useAuth();
    const theme = useMantineTheme();
    if (!currentUser) return null; // Should be caught by ProtectedRoute

    return (
        <Container className="page-container">
            <Title order={2} my="lg">Dashboard</Title>
            <Paper p="lg" shadow="xs" withBorder className="fade-in">
                <Title order={3} c={theme.primaryColor}>Welcome, {currentUser.username}!</Title>
                <Text component="span">Role: <Badge color={currentUser.role === 'parent' ? 'pink' : 'green'}>{currentUser.role}</Badge></Text>
                {currentUser.role === 'kid' && (
                    <Group mt="md" gap="xs">
                        <Text size="lg" fw={500}>Your Points:</Text>
                        <Badge variant="filled" size="xl" color="yellow" className="count-up" styles={{ root: { fontSize: '1.2rem', padding: '12px 20px' } }}>
                            {currentUser.points ?? 0}
                        </Badge>
                    </Group>
                )}
            </Paper>
            {currentUser.role === 'kid' && (
                <Box mt="lg">
                    <StreakDisplay />
                </Box>
            )}
            {currentUser.role === 'parent' && (
                <>
                    <Divider my="xl" label="Parent Controls" labelPosition="center" />
                    <Stack gap="lg">
                        <Paper withBorder p="lg"><Group gap="xs" mb="md"><IconAward size={20} color={theme.colors.yellow[7]}/><Title order={4}>Award Points</Title></Group><AwardPoints /></Paper>
                        <Paper withBorder p="lg"><Group gap="xs" mb="md"><IconSettings size={20} color={theme.colors.gray[7]}/><Title order={4}>Manage Store Items</Title></Group><ManageStoreItems /></Paper>
                        <Paper withBorder p="lg"><Group gap="xs" mb="md"><IconUserUp size={20} color={theme.colors.blue[7]}/><Title order={4}>User Management</Title></Group><UserManagement /></Paper>
                    </Stack>
                </>
            )}
        </Container>
    );
};

const StorePage = () => {
    const [items, setItems] = useState<api.StoreItem[]>([]);
    const { currentUser } = useAuth();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const theme = useMantineTheme();
    const [searchResults, setSearchResults] = useState<api.StoreItem[]>([]);

    useEffect(() => {
        setLoading(true);
        api.getStoreItems()
            .then(response => {
                const sortedItems = response.data.sort((a, b) => a.points_cost - b.points_cost);
                setItems(sortedItems);
                setSearchResults(sortedItems);
                setError(null);
            })
            .catch(err => setError("Failed to load store items."))
            .finally(() => setLoading(false));
    }, []);

    const handleSearch = (results: api.StoreItem[]) => setSearchResults(results);
    
    const handleRedeem = async (itemId: string, cost: number) => {
        if (!currentUser || currentUser.role !== 'kid' || (currentUser.points ?? 0) < cost) {
            notifications.show({ title: 'Redemption Failed', message: 'Not enough points or not a kid account!', color: 'red' });
            return;
        }
        try {
            await api.redeemItem({ item_id: itemId });
            notifications.show({ title: 'Request Sent', message: 'Redemption request sent! A parent will need to approve it.', color: 'blue' });
        } catch (err) {
            notifications.show({ title: 'Error', message: 'Failed to redeem item.', color: 'red' });
        }
    };

    if (loading) return <Center style={{ height: 'calc(100vh - 120px)' }}><LoadingOverlay visible={true} overlayProps={{ radius: "sm", blur: 2 }} /></Center>;
    if (error) return <Container><Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" radius="md" mt="lg">{error}</Alert></Container>;

    return (
        <Container>
            <Title order={2} my="lg">Rewards Store</Title>
            <SearchBar items={items} onSearch={handleSearch} />
            {searchResults.length === 0 ? <Text mt="lg">No items found.</Text> : (
                <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="lg" mt="lg">
                    {searchResults.map(item => (
                        <Card shadow="sm" padding="lg" radius="md" withBorder key={item.id} className="card-hover">
                            <Stack justify="space-between" style={{ height: '100%' }}>
                                <Box>
                                    <Group justify="space-between" mt="md" mb="xs"><Title order={3}>{item.name}</Title><Badge color={theme.colors.yellow[6]} variant="light" size="lg">{item.points_cost} Points</Badge></Group>
                                    <Text size="sm" c="dimmed" mb="md">{item.description || 'No description available.'}</Text>
                                </Box>
                                {currentUser?.role === 'kid' && <Button variant="filled" color="indigo" fullWidth mt="md" radius="md" onClick={() => handleRedeem(item.id, item.points_cost)} disabled={(currentUser.points ?? 0) < item.points_cost} leftSection={<IconShoppingCart size={16} />}>Redeem</Button>}
                            </Stack>
                        </Card>
                    ))}
                </SimpleGrid>
            )}
        </Container>
    );
};

const NotFoundPage = () => (
    <Container style={{ textAlign: 'center', marginTop: '50px' }}>
        <Title order={1}>404</Title><Text size="xl">Oops! Page Not Found.</Text>
        <Button component={RouterLink} to="/" mt="lg" variant="outline">Go Home</Button>
    </Container>
);

const ProtectedRoute: React.FC = () => { // Simplified for v6
    const { currentUser } = useAuth();
    if (currentUser === undefined) return <Center style={{ height: '100vh' }}><LoadingOverlay visible={true} /></Center>;
    return currentUser ? <Outlet /> : <Navigate to="/login" replace />;
};

const App: React.FC = () => {
    const [mobileOpened, { toggle: toggleMobile }] = useDisclosure();
    const [desktopOpened, { toggle: toggleDesktop }] = useDisclosure(true);
    const { currentUser, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const [geminiModalOpened, { open: openGeminiModal, close: closeGeminiModal }] = useDisclosure(false);
    const [geminiLoading, setGeminiLoading] = useState(false);
    const [geminiQuestion, setGeminiQuestion] = useState('');
    const [geminiAnswer, setGeminiAnswer] = useState('');
    const [geminiSuggestion, setGeminiSuggestion] = useState<any>(null);
    const [showGeminiConfirmation, setShowGeminiConfirmation] = useState(false);

    const handleLogout = () => logout();

    const resetGeminiModal = () => {
        setGeminiQuestion(''); setGeminiAnswer(''); setGeminiSuggestion(null);
        setShowGeminiConfirmation(false); setGeminiLoading(false); closeGeminiModal();
    };
    
    const handleGeminiSubmit = async () => {
        setGeminiLoading(true); setGeminiAnswer(''); setGeminiSuggestion(null); setShowGeminiConfirmation(false);
        const prompt = `You are an intelligent assistant for the "Kids Rewards" application. User's request: "${geminiQuestion}"
Analyze the user's request and determine the primary intent. Respond ONLY with a single JSON object.
Possible intents:
1. Add Shop Item: { "type": "shop_item", "name": "EXTRACTED_ITEM_NAME", "description": "...", "usd_price": PRICE_FROM_SIMULATED_SEARCH } (Identify the main item/product requested by the user for "EXTRACTED_ITEM_NAME". If the user does not specify a price, perform a simulated web search to find a reasonable USD price for "PRICE_FROM_SIMULATED_SEARCH".)
2. Add Chore: { "type": "chore", "name": "EXTRACTED_CHORE_NAME", "description": "...", "time_estimate_minutes": ESTIMATED_TIME_IN_MINUTES } (Identify the main chore/task requested by the user for "EXTRACTED_CHORE_NAME". If the user's request is vague (e.g., "a good chore"), suggest a common, specific chore like "Tidy up your room" or "Help with groceries" for "EXTRACTED_CHORE_NAME". Extract any specified time and provide it in minutes for "ESTIMATED_TIME_IN_MINUTES". If no time is specified, make a reasonable estimate in minutes for the identified or suggested chore.)
3. General Question: { "type": "general", "answer": "..." }
4. Unable to Process: { "type": "unknown", "reason": "..." }`;

        try {
            const response = await api.askGemini(prompt, geminiQuestion);
            const responseText = response.data.answer;
            let parsedResponse: any = null;
            try {
                const firstBracket = responseText.indexOf('{'); const lastBracket = responseText.lastIndexOf('}');
                if (firstBracket !== -1 && lastBracket !== -1 && lastBracket > firstBracket) {
                    parsedResponse = JSON.parse(responseText.substring(firstBracket, lastBracket + 1));
                } else { throw new Error("No JSON object found."); }
            } catch (e) { setGeminiAnswer(`Error parsing AI response: ${responseText}`); return; }

            if (!parsedResponse?.type) { setGeminiAnswer(`AI response missing type: ${responseText}`); return; }

            switch (parsedResponse.type) {
                case 'shop_item':
                    if (parsedResponse.name && typeof parsedResponse.usd_price === 'number' && parsedResponse.usd_price > 0) {
                        setGeminiSuggestion({ type: 'shop_item', name: parsedResponse.name, description: parsedResponse.description || '', usd_price: parsedResponse.usd_price, points_cost: Math.round(parsedResponse.usd_price * 35) });
                        setShowGeminiConfirmation(true);
                    } else { setGeminiAnswer(`Could not suggest shop item. AI: ${parsedResponse.reason || 'Missing name/price.'}`); }
                    break;
                case 'chore':
                    if (parsedResponse.name && typeof parsedResponse.time_estimate_minutes === 'number' && parsedResponse.time_estimate_minutes > 0) {
                        setGeminiSuggestion({ type: 'chore', name: parsedResponse.name, description: parsedResponse.description || '', time_estimate_minutes: parsedResponse.time_estimate_minutes, points_value: Math.round(parsedResponse.time_estimate_minutes * 3) });
                        setShowGeminiConfirmation(true);
                    } else { setGeminiAnswer(`Could not suggest chore. AI: ${parsedResponse.reason || 'Missing name/time.'}`); }
                    break;
                case 'general': setGeminiAnswer(parsedResponse.answer || "AI provided general response."); break;
                case 'unknown': setGeminiAnswer(`AI could not process: ${parsedResponse.reason || 'No reason.'}`); break;
                default: setGeminiAnswer(`Unexpected AI response type: ${parsedResponse.type}. Raw: ${responseText}`);
            }
        } catch (error) { setGeminiAnswer('Failed to communicate with AI.'); } 
        finally { setGeminiLoading(false); }
    };

    const handleConfirmGeminiSuggestion = async () => {
        if (!geminiSuggestion || !currentUser) { notifications.show({ title: "Error", message: "No suggestion/user.", color: "red"}); setShowGeminiConfirmation(false); return; }
        setGeminiLoading(true);
        try {
            let payload: api.KidFeatureRequestPayloadAPI; let successMessage = '';
            if (geminiSuggestion.type === 'shop_item') {
                payload = { request_type: api.RequestTypeAPI.ADD_STORE_ITEM, details: { name: geminiSuggestion.name, description: geminiSuggestion.description || `Suggested by Gemini. USD: $${geminiSuggestion.usd_price.toFixed(2)}`, points_cost: geminiSuggestion.points_cost }};
                successMessage = `Shop item request for "${geminiSuggestion.name}" sent.`;
            } else if (geminiSuggestion.type === 'chore') {
                payload = { request_type: api.RequestTypeAPI.ADD_CHORE, details: { name: geminiSuggestion.name, description: geminiSuggestion.description || `Suggested by Gemini. Time: ${geminiSuggestion.time_estimate_minutes} mins.`, points_value: geminiSuggestion.points_value }};
                successMessage = `Chore request for "${geminiSuggestion.name}" sent.`;
            } else { notifications.show({ title: "Error", message: "Invalid suggestion type.", color: "red"}); return; }

            await api.submitFeatureRequest(payload);
            notifications.show({ title: 'Request Submitted!', message: successMessage, color: 'indigo', icon: <IconChecklist size={18} /> });
            resetGeminiModal();
        } catch (err: any) { notifications.show({ title: 'Submission Failed', message: err.response?.data?.detail || `Failed to submit request.`, color: 'red', icon: <IconAlertCircle size={18} /> });
        } finally { setGeminiLoading(false); }
    };
    
    const navLinks = [
        { icon: IconHome, label: 'Dashboard', to: '/' },
        { icon: IconShoppingCart, label: 'Store', to: '/store' },
        { icon: IconListNumbers, label: 'Leaderboard', to: '/leaderboard' },
    ];

    return (
        <AppShell header={{ height: 60 }} navbar={{ width: 250, breakpoint: 'sm', collapsed: { mobile: !mobileOpened, desktop: !desktopOpened }}} padding="md">
            <AppShell.Header>
                <Group h="100%" px="md" justify="space-between">
                    <Group>
                        {currentUser && (
                            <Burger 
                                opened={mobileOpened} 
                                onClick={toggleMobile} 
                                hiddenFrom="sm" 
                                size="sm" 
                                aria-label="Toggle navigation"
                            />
                        )}
                        {currentUser && (
                            <Burger 
                                opened={desktopOpened} 
                                onClick={toggleDesktop} 
                                visibleFrom="sm" 
                                size="sm" 
                                aria-label="Toggle navigation"
                            />
                        )}
                        <RouterLink to="/" style={{ textDecoration: 'none', color: 'inherit' }}>
                            <Title order={3}>Kids Rewards</Title>
                        </RouterLink>
                    </Group>
                    
                    {currentUser ? (
                        <>
                            {/* Mobile view - simplified */}
                            <Group hiddenFrom="sm" gap="xs">
                                {currentUser.role === 'kid' && <StreakDisplay compact />}
                                <Menu 
                                    shadow="md" 
                                    width={200} 
                                    position="bottom-end"
                                    transitionProps={{ transition: 'pop-top-right' }}
                                >
                                    <Menu.Target>
                                        <ActionIcon 
                                            variant="subtle" 
                                            size="lg"
                                            aria-label="User menu"
                                        >
                                            <IconUser size={24} />
                                        </ActionIcon>
                                    </Menu.Target>

                                    <Menu.Dropdown>
                                        <Menu.Label>
                                            {currentUser.username}
                                            <Text size="xs" c="dimmed">{currentUser.role}</Text>
                                        </Menu.Label>
                                        <Menu.Divider />
                                        <Menu.Item 
                                            leftSection={<IconMessageChatbot size={16} />}
                                            onClick={() => { resetGeminiModal(); openGeminiModal(); }}
                                        >
                                            Gemini Assistant
                                        </Menu.Item>
                                        <Menu.Divider />
                                        <Menu.Item 
                                            color="red" 
                                            leftSection={<IconLogout size={16} />}
                                            onClick={handleLogout}
                                        >
                                            Logout
                                        </Menu.Item>
                                    </Menu.Dropdown>
                                </Menu>
                            </Group>

                            {/* Desktop view - full layout */}
                            <Group visibleFrom="sm">
                                <Button 
                                    onClick={() => { resetGeminiModal(); openGeminiModal(); }} 
                                    variant="gradient" 
                                    gradient={{ from: 'indigo', to: 'cyan' }} 
                                    leftSection={<IconMessageChatbot size={18}/>}
                                >
                                    Gemini Assistant
                                </Button>
                                {currentUser.role === 'kid' && <StreakDisplay compact />}
                                <Menu 
                                    shadow="md" 
                                    width={200} 
                                    position="bottom-end"
                                    transitionProps={{ transition: 'pop-top-right' }}
                                >
                                    <Menu.Target>
                                        <Button 
                                            variant="subtle" 
                                            rightSection={<IconChevronDown size={16} />}
                                        >
                                            {currentUser.username}
                                        </Button>
                                    </Menu.Target>

                                    <Menu.Dropdown>
                                        <Menu.Label>
                                            Account
                                            <Text size="xs" c="dimmed">Role: {currentUser.role}</Text>
                                        </Menu.Label>
                                        <Menu.Divider />
                                        <Menu.Item 
                                            color="red" 
                                            leftSection={<IconLogout size={16} />}
                                            onClick={handleLogout}
                                        >
                                            Logout
                                        </Menu.Item>
                                    </Menu.Dropdown>
                                </Menu>
                            </Group>
                        </>
                    ) : (
                        (location.pathname !== '/login' && location.pathname !== '/signup') && 
                        <Button component={RouterLink} to="/login" variant="default">Login</Button>
                    )}
                </Group>
            </AppShell.Header>

            {currentUser && (
                <AppShell.Navbar p="md">
                    <Stack gap="xs" style={{ height: '100%' }}>
                        {/* Gemini Assistant - prominent position on mobile */}
                        <Button
                            fullWidth
                            onClick={() => { 
                                resetGeminiModal(); 
                                openGeminiModal();
                                if (mobileOpened) toggleMobile();
                            }} 
                            variant="gradient" 
                            gradient={{ from: 'indigo', to: 'cyan' }} 
                            leftSection={<IconMessageChatbot size={20}/>}
                            hiddenFrom="sm"
                            mb="sm"
                        >
                            Gemini Assistant
                        </Button>
                        
                        {navLinks.map((link) => (
                            <NavLink 
                                key={link.label} 
                                label={link.label} 
                                leftSection={<link.icon size="1.2rem" stroke={1.5} />} 
                                component={RouterLink} 
                                to={link.to} 
                                active={location.pathname === link.to} 
                                onClick={() => { 
                                    if (mobileOpened) toggleMobile(); 
                                }}
                                styles={{
                                    label: { fontSize: '0.95rem', fontWeight: 500 },
                                }}
                            />
                        ))}
                        
                        {currentUser.role === 'kid' && (
                            <>
                                <Divider my="xs" label="My Activities" labelPosition="center" />
                                <NavLink 
                                    label="Available Chores" 
                                    leftSection={<IconChecklist size="1.2rem" stroke={1.5} />} 
                                    component={RouterLink} 
                                    to="/chores" 
                                    active={location.pathname === "/chores"} 
                                    onClick={() => { if (mobileOpened) toggleMobile(); }}
                                    styles={{ label: { fontSize: '0.95rem', fontWeight: 500 } }}
                                />
                                <NavLink 
                                    label="Assigned to Me" 
                                    leftSection={<IconUserCheck size="1.2rem" stroke={1.5} />} 
                                    component={RouterLink} 
                                    to="/my-assigned-chores" 
                                    active={location.pathname === "/my-assigned-chores"} 
                                    onClick={() => { if (mobileOpened) toggleMobile(); }}
                                    styles={{ label: { fontSize: '0.95rem', fontWeight: 500 } }}
                                />
                                <NavLink 
                                    label="Chore History" 
                                    leftSection={<IconHistory size="1.2rem" stroke={1.5} />} 
                                    component={RouterLink} 
                                    to="/chores/history" 
                                    active={location.pathname === "/chores/history"} 
                                    onClick={() => { if (mobileOpened) toggleMobile(); }}
                                    styles={{ label: { fontSize: '0.95rem', fontWeight: 500 } }}
                                />
                                <NavLink 
                                    label="🦎 Bearded Dragon Goal" 
                                    leftSection={<IconTarget size="1.2rem" stroke={1.5} />} 
                                    component={RouterLink} 
                                    to="/bearded-dragon-goal" 
                                    active={location.pathname === "/bearded-dragon-goal"} 
                                    onClick={() => { if (mobileOpened) toggleMobile(); }}
                                    styles={{ label: { fontSize: '0.95rem', fontWeight: 500 } }}
                                />
                                <NavLink 
                                    label="Purchase History" 
                                    leftSection={<IconReceipt size="1.2rem" stroke={1.5} />} 
                                    component={RouterLink} 
                                    to="/history" 
                                    active={location.pathname === "/history"} 
                                    onClick={() => { if (mobileOpened) toggleMobile(); }}
                                    styles={{ label: { fontSize: '0.95rem', fontWeight: 500 } }}
                                />
                                <NavLink 
                                    label="Make Request" 
                                    leftSection={<IconMessagePlus size="1.2rem" stroke={1.5} />} 
                                    component={RouterLink} 
                                    to="/make-request" 
                                    active={location.pathname === "/make-request"} 
                                    onClick={() => { if (mobileOpened) toggleMobile(); }}
                                    styles={{ label: { fontSize: '0.95rem', fontWeight: 500 } }}
                                />
                            </>
                        )}
                        
                        {currentUser.role === 'parent' && (
                            <>
                                <Divider my="xs" label="Management" labelPosition="center" />
                                <NavLink 
                                    label="Manage Chores" 
                                    leftSection={<IconClipboardList size="1.2rem" stroke={1.5} />} 
                                    component={RouterLink} 
                                    to="/parent/manage-chores" 
                                    active={location.pathname === "/parent/manage-chores"} 
                                    onClick={() => { if (mobileOpened) toggleMobile(); }}
                                    styles={{ label: { fontSize: '0.95rem', fontWeight: 500 } }}
                                />
                                <NavLink 
                                    label="Assign Chores" 
                                    leftSection={<IconUserCheck size="1.2rem" stroke={1.5} />} 
                                    component={RouterLink} 
                                    to="/parent/assign-chores" 
                                    active={location.pathname === "/parent/assign-chores"} 
                                    onClick={() => { if (mobileOpened) toggleMobile(); }}
                                    styles={{ label: { fontSize: '0.95rem', fontWeight: 500 } }}
                                />
                                <NavLink 
                                    label="Pending Approvals" 
                                    leftSection={<IconHourglassHigh size="1.2rem" stroke={1.5} />} 
                                    component={RouterLink} 
                                    to="/parent/pending-requests" 
                                    active={location.pathname === "/parent/pending-requests"} 
                                    onClick={() => { if (mobileOpened) toggleMobile(); }}
                                    styles={{ label: { fontSize: '0.95rem', fontWeight: 500 } }}
                                />
                                <NavLink 
                                    label="Feature Requests" 
                                    leftSection={<IconListCheck size="1.2rem" stroke={1.5} />} 
                                    component={RouterLink} 
                                    to="/manage-requests" 
                                    active={location.pathname === "/manage-requests"} 
                                    onClick={() => { if (mobileOpened) toggleMobile(); }}
                                    styles={{ label: { fontSize: '0.95rem', fontWeight: 500 } }}
                                />
                                <NavLink 
                                    label="🦎 Bearded Dragon Goal" 
                                    leftSection={<IconTarget size="1.2rem" stroke={1.5} />} 
                                    component={RouterLink} 
                                    to="/bearded-dragon-goal" 
                                    active={location.pathname === "/bearded-dragon-goal"} 
                                    onClick={() => { if (mobileOpened) toggleMobile(); }}
                                    styles={{ label: { fontSize: '0.95rem', fontWeight: 500 } }}
                                />
                            </>
                        )}
                        
                        {/* User info at bottom on mobile */}
                        <Box mt="auto" pt="md" hiddenFrom="sm">
                            <Divider mb="sm" />
                            <Group justify="space-between">
                                <Box>
                                    <Text size="sm" fw={600}>{currentUser.username}</Text>
                                    <Text size="xs" c="dimmed">{currentUser.role}</Text>
                                    {currentUser.role === 'kid' && (
                                        <Badge mt={4} size="sm" color="yellow">
                                            {currentUser.points ?? 0} points
                                        </Badge>
                                    )}
                                </Box>
                                <ActionIcon 
                                    color="red" 
                                    variant="subtle"
                                    onClick={handleLogout}
                                    size="lg"
                                    aria-label="Logout"
                                >
                                    <IconLogout size={20} />
                                </ActionIcon>
                            </Group>
                        </Box>
                    </Stack>
                </AppShell.Navbar>
            )}

            <Modal opened={geminiModalOpened} onClose={resetGeminiModal} title="Gemini Assistant" size="xl">
                <LoadingOverlay visible={geminiLoading} overlayProps={{ blur: 2, radius: "sm" }} />
                {!showGeminiConfirmation && (
                    <Stack>
                        <Textarea label="Your request to Gemini" placeholder="e.g., 'Find a cool Lego set under $50' or 'Create a chore for tidying the playroom, it takes about 30 mins'" value={geminiQuestion} onChange={(event: React.ChangeEvent<HTMLTextAreaElement>) => setGeminiQuestion(event.currentTarget.value)} minRows={3} autosize />
                        <Button onClick={handleGeminiSubmit} loading={geminiLoading} disabled={!geminiQuestion.trim()}>Ask Gemini</Button>
                        {geminiAnswer && !geminiSuggestion && (<Paper p="md" shadow="xs" withBorder mt="md" radius="md"><Text fw={500} mb="xs">Gemini's Response:</Text><Textarea value={geminiAnswer} readOnly autosize minRows={3} maxRows={10} styles={{ input: { fontFamily: 'monospace' } }} /></Paper>)}
                    </Stack>
                )}
                {showGeminiConfirmation && geminiSuggestion && (
                    <Stack>
                        <Title order={4} mb="sm">Confirm Suggestion</Title>
                        {geminiSuggestion.type === 'shop_item' && (<Paper p="md" shadow="xs" withBorder radius="md"><Text><strong>Item:</strong> {geminiSuggestion.name}</Text>{geminiSuggestion.description && <Text size="sm" c="dimmed" mt={4}><strong>Description:</strong> {geminiSuggestion.description}</Text>}<Text mt={4}><strong>Estimated Price:</strong> ${geminiSuggestion.usd_price?.toFixed(2)}</Text><Text fw={700} c="teal" mt={4}><strong>Calculated Points:</strong> {geminiSuggestion.points_cost}</Text></Paper>)}
                        {geminiSuggestion.type === 'chore' && (<Paper p="md" shadow="xs" withBorder radius="md"><Text><strong>Chore:</strong> {geminiSuggestion.name}</Text>{geminiSuggestion.description && <Text size="sm" c="dimmed" mt={4}><strong>Description:</strong> {geminiSuggestion.description}</Text>}<Text mt={4}><strong>Estimated Time:</strong> {geminiSuggestion.time_estimate_minutes} minutes</Text><Text fw={700} c="teal" mt={4}><strong>Calculated Points:</strong> {geminiSuggestion.points_value}</Text></Paper>)}
                        <Group mt="xl" style={{justifyContent: 'flex-end'}}><Button variant="default" onClick={() => setShowGeminiConfirmation(false)}>Cancel / Modify</Button><Button onClick={handleConfirmGeminiSuggestion} loading={geminiLoading}>Confirm & Submit</Button></Group>
                    </Stack>
                )}
            </Modal>

            <AppShell.Main>
                <Routes>
                    <Route path="/login" element={currentUser ? <Navigate to="/" replace /> : <LoginPage />} />
                    <Route path="/signup" element={currentUser ? <Navigate to="/" replace /> : <SignupPage />} />
                    <Route element={<ProtectedRoute />}>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/store" element={<StorePage />} />
                        <Route path="/leaderboard" element={<LeaderboardPage />} />
                        <Route path="/history" element={<PurchaseHistoryPage />} />
                        <Route path="/parent/pending-requests" element={<PendingRequestsPage />} />
                        <Route path="/parent/manage-chores" element={<ManageChoresPage />} />
                        <Route path="/chores" element={<ChoresPage />} />
                        <Route path="/my-assigned-chores" element={<MyAssignedChoresPage />} />
                        <Route path="/chores/history" element={<ChoreHistoryPage />} />
                        <Route path="/make-request" element={<MakeRequestPage />} />
                        <Route path="/manage-requests" element={<ManageRequestsPage />} />
                        <Route path="/parent/assign-chores" element={<AssignChoresPage />} />
                        <Route path="/bearded-dragon-goal" element={<BeardedDragonGoalPage />} />
                    </Route>
                    <Route path="*" element={<NotFoundPage />} />
                </Routes>
            </AppShell.Main>
        </AppShell>
    );
};

const AppWithAuthProvider = () => {
    const [currentUser, setCurrentUser] = useState<api.User | null | undefined>(undefined);
    const navigate = useNavigate(); 

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            api.getCurrentUser().then(response => setCurrentUser(response.data)).catch(() => {
                localStorage.removeItem('token'); setCurrentUser(null);
            });
        } else { setCurrentUser(null); }
    }, []);

    const logout = () => {
        localStorage.removeItem('token'); setCurrentUser(null); navigate('/login');
    };
    
    if (currentUser === undefined) return <Center style={{ height: '100vh' }}><LoadingOverlay visible={true} /></Center>;
    
    return <AuthContext.Provider value={{ currentUser, setCurrentUser, logout }}><App /></AuthContext.Provider>;
};

const theme = createTheme({
  fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  primaryColor: 'indigo',
  colors: {
    brand: ['#f3f0ff', '#e5dbff', '#d0bfff', '#b197fc', '#9775fa', '#845ef7', '#7950f2', '#703fec', '#6741d9', '#5f3dc4'],
  },
  fontSizes: {
    xs: '0.875rem',
    sm: '0.95rem',
    md: '1.05rem',
    lg: '1.2rem',
    xl: '1.4rem',
  },
  components: {
    Button: { 
      defaultProps: { radius: 'md' },
      styles: {
        root: {
          transition: 'all 0.2s ease',
          '&:hover': {
            transform: 'translateY(-1px)',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          },
        },
      },
    },
    Paper: { 
      defaultProps: { radius: 'md' },
      styles: {
        root: {
          transition: 'all 0.2s ease',
        },
      },
    },
    Card: {
      styles: {
        root: {
          transition: 'all 0.2s ease',
        },
      },
    },
    NavLink: {
      styles: {
        root: {
          borderRadius: '8px',
          transition: 'all 0.2s ease',
          '&:hover': {
            backgroundColor: 'var(--mantine-color-indigo-0)',
          },
          '&[data-active]': {
            backgroundColor: 'var(--mantine-color-indigo-1)',
            color: 'var(--mantine-color-indigo-7)',
            fontWeight: 600,
          },
        },
      },
    },
    Title: { styles: (theme: MantineTheme) => ({ root: { fontWeight: 700 } })},
    Textarea: { defaultProps: { radius: 'sm' }},
  },
  other: {
    transitions: {
      fast: '0.15s ease',
      normal: '0.2s ease',
      slow: '0.3s ease',
    },
  },
});

const AppWrapper = () => (
    <Router>
        <MantineProvider theme={theme} defaultColorScheme="light">
            <Notifications />
            <AppWithAuthProvider />
        </MantineProvider>
    </Router>
);

export default AppWrapper;

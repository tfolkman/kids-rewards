import React, { useState, useEffect, createContext, useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Link as RouterLink, Navigate, Outlet, useNavigate, useLocation } from 'react-router';
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
    Select,
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
    Modal
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { Notifications } from '@mantine/notifications'; // Import Notifications
import { IconAlertCircle, IconLogin, IconUserPlus, IconHome, IconShoppingCart, IconLogout, IconSettings, IconAward, IconUserUp, IconListNumbers, IconReceipt, IconHourglassHigh, IconClipboardList, IconHistory, IconChecklist, IconMessagePlus, IconListCheck } from '@tabler/icons-react'; // Added chore and request icons
import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css'; // Import notifications styles
import './App.css';
import * as api from './services/api';
import ManageStoreItems from './components/ManageStoreItems';
import AwardPoints from './components/AwardPoints';
import UserManagement from './components/UserManagement'; // Import UserManagement
import SearchBar from './components/SearchBar';
import LeaderboardPage from './pages/LeaderboardPage'; // Import the new page
import PurchaseHistoryPage from './pages/PurchaseHistoryPage'; // Import PurchaseHistoryPage
import PendingRequestsPage from './pages/PendingRequestsPage'; // Import PendingRequestsPage
import ManageChoresPage from './pages/ManageChoresPage';
import ChoresPage from './pages/ChoresPage';
import ChoreHistoryPage from './pages/ChoreHistoryPage';
import MakeRequestPage from './pages/MakeRequestPage'; // Import MakeRequestPage
import ManageRequestsPage from './pages/ManageRequestsPage'; // Import ManageRequestsPage

// --- Context for Auth ---
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

// --- Page Components (Refactored with Mantine) ---
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
            // Pass username and password directly to api.login
            const response = await api.login(username, password);
            localStorage.setItem('token', response.data.access_token);
            const userResponse = await api.getCurrentUser();
            setCurrentUser(userResponse.data);
            navigate('/');
        } catch (err) {
            setError('Failed to login. Check credentials.');
            console.error(err);
        } finally {
            setLoading(false);
            try {
                const helloResponse = await api.helloWorld();
                console.log("Hello response:", helloResponse.data.message);
            } catch (helloErr) {
                console.error("Error calling hello endpoint:", helloErr);
            }
        }
    };

    return (
        <Container size="xs" style={{ marginTop: '50px' }}>
            <Paper withBorder shadow="md" p={30} mt={30} radius="md">
                <Title ta="center" order={2} mb="lg">Welcome Back!</Title>
                <form onSubmit={handleSubmit}>
                    <Stack>
                        <TextInput
                            required
                            label="Username"
                            placeholder="Your username"
                            value={username}
                            onChange={(event) => setUsername(event.currentTarget.value)}
                        />
                        <PasswordInput
                            required
                            label="Password"
                            placeholder="Your password"
                            value={password}
                            onChange={(event) => setPassword(event.currentTarget.value)}
                        />
                        {error && (
                            <Alert icon={<IconAlertCircle size="1rem" />} title="Login Error" color="red" radius="md">
                                {error}
                            </Alert>
                        )}
                        <Button type="submit" fullWidth mt="xl" loading={loading} leftSection={<IconLogin size={16} />}>
                            Login
                        </Button>
                    </Stack>
                </form>
                <Text ta="center" mt="md">
                    Don't have an account?{' '}
                    <RouterLink to="/signup" style={{ textDecoration: 'none' }}>
                         <Text component="span" c="teal" fw={500}>Sign Up</Text>
                    </RouterLink>
                </Text>
            </Paper>
        </Container>
    );
};

const SignupPage = () => {
    const navigate = useNavigate();
    const { setCurrentUser } = useAuth();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    // const [role, setRole] = useState<'parent' | 'kid'>('kid'); // Role is now fixed to 'kid' on signup
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);
        try {
            // Role is no longer sent from frontend, backend will default to 'kid'
            // UserCreate interface in api.ts no longer has 'role'
            await api.signup({ username, password });
            // Pass username and password directly to api.login after successful signup
            const tokenResponse = await api.login(username, password);
            localStorage.setItem('token', tokenResponse.data.access_token);
            const userResponse = await api.getCurrentUser();
            setCurrentUser(userResponse.data);
            navigate('/');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to sign up.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container size="xs" style={{ marginTop: '50px' }}>
            <Paper withBorder shadow="md" p={30} mt={30} radius="md">
                <Title ta="center" order={2} mb="lg">Create Your Account</Title>
                <form onSubmit={handleSubmit}>
                    <Stack>
                        <TextInput
                            required
                            label="Username"
                            placeholder="Choose a username"
                            value={username}
                            onChange={(event) => setUsername(event.currentTarget.value)}
                        />
                        <PasswordInput
                            required
                            label="Password"
                            placeholder="Choose a password"
                            value={password}
                            onChange={(event) => setPassword(event.currentTarget.value)}
                        />
                        {/* Role selection removed */}
                        {error && (
                             <Alert icon={<IconAlertCircle size="1rem" />} title="Signup Error" color="red" radius="md">
                                {error}
                            </Alert>
                        )}
                        <Button type="submit" fullWidth mt="xl" loading={loading} leftSection={<IconUserPlus size={16}/>}>
                            Sign Up
                        </Button>
                    </Stack>
                </form>
                <Text ta="center" mt="md">
                    Already have an account?{' '}
                     <RouterLink to="/login" style={{ textDecoration: 'none' }}>
                        <Text component="span" c="teal" fw={500}>Login</Text>
                    </RouterLink>
                </Text>
            </Paper>
        </Container>
    );
};

const Dashboard = () => {
    const { currentUser } = useAuth();
    const theme = useMantineTheme();

    if (currentUser === undefined) return (
        <Center style={{ height: '100vh' }}>
            <LoadingOverlay visible={true} overlayProps={{ radius: "sm", blur: 2 }} />
        </Center>
    );
    if (!currentUser) return <Navigate to="/login" replace />;

    return (
        <Container>
            <Title order={2} my="lg">Dashboard</Title>
            <Paper p="lg" shadow="xs" withBorder>
                <Title order={3} c={theme.primaryColor}>Welcome, {currentUser.username}!</Title>
                <Text component="span">Role: <Badge color={currentUser.role === 'parent' ? 'pink' : 'green'}>{currentUser.role}</Badge></Text>
                {currentUser.role === 'kid' && (
                    <Text component="span" mt="sm" size="lg">Your Points: <Badge variant="filled" size="xl" color="yellow">{currentUser.points ?? 0}</Badge></Text>
                )}
            </Paper>

            {currentUser.role === 'parent' && (
                <>
                    <Divider my="xl" label="Parent Controls" labelPosition="center" />
                    <Stack gap="lg">
                        <Paper>
                            <Group gap="xs" mb="md">
                                <IconAward size={20} color={theme.colors.yellow[7]}/>
                                <Title order={4}>Award Points</Title>
                            </Group>
                            <AwardPoints />
                        </Paper>
                        <Paper>
                            <Group gap="xs" mb="md">
                                <IconSettings size={20} color={theme.colors.gray[7]}/>
                                <Title order={4}>Manage Store Items</Title>
                            </Group>
                            <ManageStoreItems />
                        </Paper>
                        <Paper>
                            <Group gap="xs" mb="md">
                                <IconUserUp size={20} color={theme.colors.blue[7]}/> {/* Changed Icon */}
                                <Title order={4}>User Management</Title>
                            </Group>
                            <UserManagement />
                        </Paper>
                    </Stack>
                </>
            )}
        </Container>
    );
};

const StorePage = () => {
    const [items, setItems] = useState<api.StoreItem[]>([]);
    const { currentUser, setCurrentUser } = useAuth();
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
                setError(null);
            })
            .catch(err => {
                console.error("Error fetching store items:", err);
                setError("Failed to load store items.");
            })
            .finally(() => setLoading(false));
    }, []);

    const handleSearch = (results: api.StoreItem[]) => {
        setSearchResults(results);
    };
    
    useEffect(() => {
        setSearchResults(items);
    }, [items]);

    const handleRedeem = async (itemId: string, cost: number) => {
        if (!currentUser || currentUser.role !== 'kid' || (currentUser.points ?? 0) < cost) {
            alert("Not enough points or not a kid account!"); // TODO: Replace with Mantine notification
            return;
        }
        try {
            // The redeemItem function now returns a PurchaseLog, not a User.
            // It also initiates a pending request, so points aren't immediately deducted.
            await api.redeemItem({ item_id: itemId });
            // TODO: Replace alert with a Mantine notification for better UX
            alert("Redemption request sent! A parent will need to approve it.");
            // No longer setting current user here as points don't change immediately.
            // The user's points will update after parent approval and subsequent data refresh.
        } catch (err) {
            console.error("Error redeeming item:", err);
            alert("Failed to redeem item."); // TODO: Replace with Mantine notification
        }
    };

    if (loading) return (
        <Center style={{ height: 'calc(100vh - 120px)' }}>
             <LoadingOverlay visible={true} overlayProps={{ radius: "sm", blur: 2 }} />
        </Center>
    );
    if (error) return (
        <Container>
            <Alert icon={<IconAlertCircle size="1rem" />} title="Error" color="red" radius="md" mt="lg">
                {error}
            </Alert>
        </Container>
    );

    return (
        <Container>
            <Title order={2} my="lg">Rewards Store</Title>
            <SearchBar items={items} onSearch={handleSearch} />
            {searchResults.length === 0 ? (
                <Text>No items found.</Text>
            ) : (
                <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="lg">
                    {searchResults.map(item => (
                        <Card shadow="sm" padding="lg" radius="md" withBorder key={item.id}>
                            <Stack justify="space-between" style={{ height: '100%' }}>
                                <Box>
                                    <Group justify="space-between" mt="md" mb="xs">
                                        <Title order={3}>{item.name}</Title>
                                        <Badge color={theme.colors.yellow[6]} variant="light" size="lg">
                                            {item.points_cost} Points
                                        </Badge>
                                    </Group>
                                    <Text size="sm" c="dimmed" mb="md">
                                        {item.description || 'No description available.'}
                                    </Text>
                                </Box>
                                {currentUser && currentUser.role === 'kid' && (
                                    <Button
                                        variant="filled"
                                        color="teal"
                                        fullWidth
                                        mt="md"
                                        radius="md"
                                        onClick={() => handleRedeem(item.id, item.points_cost)}
                                        disabled={(currentUser.points ?? 0) < item.points_cost}
                                        leftSection={<IconShoppingCart size={16} />}
                                    >
                                        Redeem
                                    </Button>
                                )}
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
        <Title order={1}>404</Title>
        <Text size="xl">Oops! Page Not Found.</Text>
        <Button component={RouterLink} to="/" mt="lg" variant="outline">Go Home</Button>
    </Container>
);

const ProtectedRoute: React.FC = () => {
    const { currentUser } = useAuth();
    return currentUser ? <Outlet /> : <Navigate to="/login" replace />;
};

const App: React.FC = () => {
    const [mobileOpened, { toggle: toggleMobile }] = useDisclosure();
    const [desktopOpened, { toggle: toggleDesktop }] = useDisclosure(true);
    const { currentUser, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const [geminiModalOpened, setGeminiModalOpened] = useState(false);
    const [question, setQuestion] = useState('');
    const [answer, setAnswer] = useState('');

    const handleLogout = () => {
        logout();
    };

    const handleSubmit = async () => {
        console.log('handleSubmit: Start. Question:', question);
        console.log('handleSubmit: Setting answer to "Analyzing your request..."');
        setAnswer('Analyzing your request...'); // Provide immediate feedback
        try {
            const prompt = `Analyze the following user request and respond ONLY with the requested JSON. Do NOT include any other text, explanations, or conversational filler. Respond in the format: ###JSON###{...}###JSON###.
If the user is asking to add a new shop item:
1.  Identify the item name.
2.  If the user mentions a specific price or a link to a product page, extract the price in US dollars.
3.  If the user mentions a general item (e.g., "a new Lego set", "a Barbie doll"), try to determine a common or average price for such an item in US dollars. If you find multiple prices, calculate their average. For subscription-based items (e.g., "Spotify subscription", "Netflix subscription") where different tiers exist, if the user does not specify a tier, assume they mean the standard/basic individual monthly plan and use its current price in US dollars. The price should be a number.
4.  Respond in a JSON format with "action": "add_shop_item", "item_name": "the name of the item", and "usd_price": the determined price in US dollars as a number.
If the user is asking a general question, respond in a JSON format with "action": "answer", and "answer": "the answer to the question".
If you cannot understand the request or cannot determine an item name or a valid USD price for a shop item request, respond with "action": "unknown".

User request: ${question}`;
            const response = await api.askGemini(prompt, question);
            
            const responseText = response.data.answer;
            const firstBracket = responseText.indexOf('{');
            const lastBracket = responseText.lastIndexOf('}');
            let geminiResponse = null; 

            if (firstBracket !== -1 && lastBracket !== -1 && lastBracket > firstBracket) {
                const jsonString = responseText.substring(firstBracket, lastBracket + 1);
                try {
                    geminiResponse = JSON.parse(jsonString);
                } catch (parseError) {
                    console.error('handleSubmit: Failed to parse extracted string as JSON:', parseError, 'String was:', jsonString);
                }
            }
            console.log('handleSubmit: Parsed Gemini response object:', geminiResponse);

            if (!geminiResponse) {
                console.error('handleSubmit: Could not find or parse JSON object in Gemini response. Full response text:', responseText);
                console.log('handleSubmit: Setting answer to "Could not process your request..." (due to parsing failure or empty response)');
                setAnswer(`Could not process your request. Gemini's response was not in the expected format.\n\nFull response: ${responseText}`);
                return; 
            }

            if (geminiResponse.action === 'add_shop_item') {
                if (geminiResponse.item_name && typeof geminiResponse.usd_price === 'number' && geminiResponse.usd_price > 0) {
                    const pointsCost = Math.round(geminiResponse.usd_price * 35);
                    
                    if (currentUser && currentUser.role === 'parent') {
                        console.log('handleSubmit: Parent path. Setting answer to "Adding..."');
                        setAnswer(`Adding "${geminiResponse.item_name}" (USD ${geminiResponse.usd_price.toFixed(2)}) for ${pointsCost} points to the store...`);
                        try {
                            await api.createStoreItem({
                                name: geminiResponse.item_name,
                                points_cost: pointsCost,
                                description: `Added via Gemini. Original USD price: $${geminiResponse.usd_price.toFixed(2)}`,
                            });
                            console.log('handleSubmit: Parent path. Setting answer to "Successfully added..."');
                            setAnswer(`Successfully added "${geminiResponse.item_name}" to the store for ${pointsCost} points.`);
                        } catch (createError) {
                            console.error('handleSubmit: Parent path. Error creating store item:', createError);
                            console.log('handleSubmit: Parent path. Setting answer to "Error adding..."');
                            setAnswer(`Error adding "${geminiResponse.item_name}" to the store.`);
                        }
                    } else {
                        console.log('handleSubmit: Kid path. Setting answer to "Requesting..."');
                        setAnswer(`Requesting to add "${geminiResponse.item_name}" (USD ${geminiResponse.usd_price.toFixed(2)}) for ${pointsCost} points... This will require parental approval.`);
                        try {
                            await api.submitFeatureRequest({
                                request_type: api.RequestTypeAPI.ADD_STORE_ITEM,
                                details: {
                                    name: geminiResponse.item_name,
                                    points_cost: pointsCost,
                                    description: `Requested based on USD price: $${geminiResponse.usd_price.toFixed(2)}`,
                                }
                            });
                            console.log('handleSubmit: Kid path. Setting answer to "Successfully submitted..."');
                            setAnswer(`Successfully submitted a request to add "${geminiResponse.item_name}" for ${pointsCost} points. A parent will need to approve it.`);
                        } catch (createError) {
                            console.error('handleSubmit: Kid path. Error submitting feature request:', createError);
                            console.log('handleSubmit: Kid path. Setting answer to "Error submitting..."');
                            setAnswer(`Error submitting request to add "${geminiResponse.item_name}".`);
                        }
                    }
                } else {
                    console.error('handleSubmit: add_shop_item path. Gemini response missing required fields (item_name, usd_price) or usd_price is invalid. Response:', geminiResponse);
                    console.log('handleSubmit: add_shop_item path. Setting answer to "Could not extract item name or a valid USD price..."');
                    setAnswer('Could not extract item name or a valid USD price from your request. Please check the console for details from Gemini.');
                }
            } else if (geminiResponse && geminiResponse.action === 'answer') {
                console.log('handleSubmit: Answer path. Setting answer from Gemini.');
                setAnswer(geminiResponse.answer);
            } else {
                console.error('handleSubmit: Unknown action or invalid response structure from Gemini. Response:', geminiResponse);
                console.log('handleSubmit: Setting answer to "Received an unknown or improperly structured response..."');
                setAnswer('Received an unknown or improperly structured response from Gemini.');
            }
        } catch (error) { 
            console.error('handleSubmit: Error in outer try block (e.g., api.askGemini call failed):', error);
            console.log('handleSubmit: Outer catch. Setting answer to "Failed to communicate with Gemini..."');
            setAnswer('Failed to communicate with Gemini or process its response. Please try again.');
        }
        console.log('handleSubmit: End');
    };
    
    const navLinks = [
        { icon: IconHome, label: 'Dashboard', to: '/' },
        { icon: IconShoppingCart, label: 'Store', to: '/store' },
        { icon: IconListNumbers, label: 'Leaderboard', to: '/leaderboard' },
        { icon: IconMessagePlus, label: 'Gemini', to: '/gemini' },
        // Purchase History will be added conditionally below for kids
    ];

    return (
        <AppShell
            header={{ height: 60 }}
            navbar={{
                width: 250,
                breakpoint: 'sm',
                collapsed: { mobile: !mobileOpened, desktop: !desktopOpened },
            }}
            padding="md"
        >
            <AppShell.Header>
                <Group h="100%" px="md" justify="space-between">
                    <Group>
                        {currentUser && (
                            <>
                                <Burger opened={mobileOpened} onClick={toggleMobile} hiddenFrom="sm" size="sm" />
                                <Burger opened={desktopOpened} onClick={toggleDesktop} visibleFrom="sm" size="sm" />
                            </>
                        )}
                        <Title order={3}>Kids Rewards</Title>
                    </Group>
                    {currentUser ? (
                         <Button variant="outline" onClick={handleLogout} leftSection={<IconLogout size={16}/>}>Logout</Button>
                    ) : (
                        (location.pathname !== '/login' && location.pathname !== '/signup') && (
                            <Button component={RouterLink} to="/login" variant="default">Login</Button>
                        )
                    )}
                </Group>
            </AppShell.Header>

            {currentUser && (
                <AppShell.Navbar p="md">
                    {navLinks.map((link) => (
                        <NavLink
                            key={link.label}
                            label={link.label}
                            leftSection={<link.icon size="1rem" stroke={1.5} />}
                            component={RouterLink}
                            to={link.to} // Use the link's 'to' prop for navigation
                            active={location.pathname === link.to}
                            onClick={(e) => {
                                if (link.label === 'Gemini') {
                                    e.preventDefault(); // Prevent default navigation only for Gemini link
                                    setGeminiModalOpened(true);
                                }
                                // For all links, close the mobile menu if it's open
                                if (mobileOpened) toggleMobile();
                            }}
                        />
                    ))}
                    {currentUser.role === 'kid' && (
                        <>
                            <NavLink
                                key="Chores"
                                label="Chores"
                                leftSection={<IconChecklist size="1rem" stroke={1.5} />}
                                component={RouterLink}
                                to="/chores"
                                active={location.pathname === "/chores"}
                                onClick={() => {
                                    navigate("/chores");
                                    if (mobileOpened) toggleMobile();
                                }}
                            />
                            <NavLink
                                key="Chore History"
                                label="Chore History"
                                leftSection={<IconHistory size="1rem" stroke={1.5} />}
                                component={RouterLink}
                                to="/chores/history"
                                active={location.pathname === "/chores/history"}
                                onClick={() => {
                                    navigate("/chores/history");
                                    if (mobileOpened) toggleMobile();
                                }}
                            />
                            <NavLink
                                key="Purchase History"
                                label="Purchase History"
                                leftSection={<IconReceipt size="1rem" stroke={1.5} />}
                                component={RouterLink}
                                to="/history"
                                active={location.pathname === "/history"}
                                onClick={() => {
                                    navigate("/history");
                                    if (mobileOpened) toggleMobile();
                                }}
                            />
                            <NavLink
                                key="Make Request"
                                label="Make a Request"
                                leftSection={<IconMessagePlus size="1rem" stroke={1.5} />}
                                component={RouterLink}
                                to="/make-request"
                                active={location.pathname === "/make-request"}
                                onClick={() => {
                                    navigate("/make-request");
                                    if (mobileOpened) toggleMobile();
                                }}
                            />
                        </>
                    )}
                    {currentUser.role === 'parent' && (
                        <>
                            <NavLink
                                label="Parent Dashboard"
                                leftSection={<IconSettings size="1rem" stroke={1.5} />}
                                component={RouterLink}
                                to="/" // Links to Dashboard where parent tools are
                                active={location.pathname === "/"}
                                 onClick={() => {
                                    navigate("/");
                                    if (mobileOpened) toggleMobile();
                                }}
                            />
                            <NavLink
                                label="Manage Chores"
                                leftSection={<IconClipboardList size="1rem" stroke={1.5} />}
                                component={RouterLink}
                                to="/parent/manage-chores"
                                active={location.pathname === "/parent/manage-chores"}
                                onClick={() => {
                                    navigate("/parent/manage-chores");
                                    if (mobileOpened) toggleMobile();
                                }}
                            />
                            <NavLink
                                label="Pending Requests"
                                leftSection={<IconHourglassHigh size="1rem" stroke={1.5} />}
                                component={RouterLink}
                                to="/parent/pending-requests"
                                active={location.pathname === "/parent/pending-requests"}
                                onClick={() => {
                                    navigate("/parent/pending-requests");
                                    if (mobileOpened) toggleMobile();
                                }}
                            />
                            <NavLink
                                label="Manage Feature Requests"
                                leftSection={<IconListCheck size="1rem" stroke={1.5} />}
                                component={RouterLink}
                                to="/manage-requests"
                                active={location.pathname === "/manage-requests"}
                                onClick={() => {
                                    navigate("/manage-requests");
                                    if (mobileOpened) toggleMobile();
                                }}
                            />
                        </>
                    )}
                </AppShell.Navbar>
            )}

            <Modal
                opened={geminiModalOpened}
                onClose={() => setGeminiModalOpened(false)}
                title="Ask Gemini"
            >
                <Stack>
                    <TextInput
                        label="Question"
                        placeholder="Ask a question"
                        value={question}
                        onChange={(e) => setQuestion(e.currentTarget.value)}
                    />
                    {answer && (
                        <Text mt="md">
                            <strong>Answer:</strong> {answer}
                        </Text>
                    )}
                    <Button onClick={() => handleSubmit()}>Submit</Button>
                </Stack>
            </Modal>

            <AppShell.Main>
                <Routes>
                    <Route path="/login" element={currentUser ? <Navigate to="/" /> : <LoginPage />} />
                    <Route path="/signup" element={currentUser ? <Navigate to="/" /> : <SignupPage />} />
                    <Route element={<ProtectedRoute />}>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/store" element={<StorePage />} />
                        <Route path="/leaderboard" element={<LeaderboardPage />} />
                        <Route path="/history" element={<PurchaseHistoryPage />} />
                        {/* Parent Routes */}
                        <Route path="/parent/pending-requests" element={<PendingRequestsPage />} />
                        <Route path="/parent/manage-chores" element={<ManageChoresPage />} />
                        {/* Kid Routes */}
                        <Route path="/chores" element={<ChoresPage />} />
                        <Route path="/chores/history" element={<ChoreHistoryPage />} />
                        <Route path="/make-request" element={<MakeRequestPage />} /> {/* Route for kids to make requests */}
                        <Route path="/manage-requests" element={<ManageRequestsPage />} /> {/* Route for parents to manage requests */}
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
            api.getCurrentUser()
                .then(response => setCurrentUser(response.data))
                .catch(() => {
                    localStorage.removeItem('token');
                    setCurrentUser(null);
                });
        } else {
            setCurrentUser(null);
        }
    }, []);

    const logout = () => {
        localStorage.removeItem('token');
        setCurrentUser(null);
        navigate('/login');
    };
    
    if (currentUser === undefined) {
        return (
            <Center style={{ height: '100vh' }}>
                <LoadingOverlay visible={true} overlayProps={{ radius: "sm", blur: 2 }} />
            </Center>
        );
    }
    
    return (
        <AuthContext.Provider value={{ currentUser, setCurrentUser, logout }}>
            <App />
        </AuthContext.Provider>
    );
};

const theme = createTheme({
  fontFamily: 'Open Sans, sans-serif',
  primaryColor: 'teal',
  components: {
    Button: {
      defaultProps: {
        radius: 'md',
      },
    },
    Paper: {
        defaultProps: {
            shadow: 'sm',
            radius: 'md',
            p: 'lg'
        }
    },
    Title: {
        styles: (theme: MantineTheme) => ({ // Added MantineTheme type
            root: {
                // color: theme.colors.teal[7], 
            }
        })
    }
  }
});

const AppWrapper = () => (
    <MantineProvider theme={theme} defaultColorScheme="light">
        <Notifications />
        <Router>
            <AppWithAuthProvider />
        </Router>
    </MantineProvider>
);

export default AppWrapper;

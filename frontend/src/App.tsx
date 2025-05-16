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
    MantineTheme
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconAlertCircle, IconLogin, IconUserPlus, IconHome, IconShoppingCart, IconLogout, IconSettings, IconAward, IconUserUp, IconListNumbers } from '@tabler/icons-react'; // Added IconUserUp and IconListNumbers
import '@mantine/core/styles.css';
import './App.css';
import * as api from './services/api';
import ManageStoreItems from './components/ManageStoreItems';
import AwardPoints from './components/AwardPoints';
import UserManagement from './components/UserManagement'; // Import UserManagement
import LeaderboardPage from './pages/LeaderboardPage'; // Import the new page

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

    const handleRedeem = async (itemId: string, cost: number) => {
        if (!currentUser || currentUser.role !== 'kid' || (currentUser.points ?? 0) < cost) {
            alert("Not enough points or not a kid account!"); // TODO: Replace with Mantine notification
            return;
        }
        try {
            const response = await api.redeemItem({ item_id: itemId });
            alert("Item redeemed successfully!"); // TODO: Replace with Mantine notification
            setCurrentUser(response.data);
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
            {items.length === 0 ? (
                <Text>No items in the store yet. Ask a parent to add some!</Text>
            ) : (
                <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }} spacing="lg">
                    {items.map(item => (
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

    const handleLogout = () => {
        logout();
    };
    
    const navLinks = [
        { icon: IconHome, label: 'Dashboard', to: '/' },
        { icon: IconShoppingCart, label: 'Store', to: '/store' },
        { icon: IconListNumbers, label: 'Leaderboard', to: '/leaderboard' },
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
                            to={link.to}
                            active={location.pathname === link.to}
                            onClick={() => {
                                navigate(link.to);
                                if (mobileOpened) toggleMobile();
                            }}
                        />
                    ))}
                    {currentUser.role === 'parent' && (
                        <NavLink
                            label="Parent Controls" // Changed label for clarity
                            leftSection={<IconSettings size="1rem" stroke={1.5} />}
                            component={RouterLink}
                            to="/" // Links to Dashboard where parent tools are
                            active={location.pathname === "/"}
                             onClick={() => {
                                navigate("/");
                                if (mobileOpened) toggleMobile();
                            }}
                        />
                    )}
                </AppShell.Navbar>
            )}

            <AppShell.Main>
                <Routes>
                    <Route path="/login" element={currentUser ? <Navigate to="/" /> : <LoginPage />} />
                    <Route path="/signup" element={currentUser ? <Navigate to="/" /> : <SignupPage />} />
                    <Route element={<ProtectedRoute />}>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/store" element={<StorePage />} />
                        <Route path="/leaderboard" element={<LeaderboardPage />} />
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
        <Router>
            <AppWithAuthProvider />
        </Router>
    </MantineProvider>
);

export default AppWrapper;

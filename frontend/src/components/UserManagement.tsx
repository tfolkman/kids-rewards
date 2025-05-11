import React, { useState } from 'react';
import { TextInput, Button, Stack, Title, Text, Alert, Paper } from '@mantine/core';
import { IconUserUp, IconAlertCircle } from '@tabler/icons-react';
import * as api from '../services/api';

const UserManagement: React.FC = () => {
    const [usernameToPromote, setUsernameToPromote] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);

    const handlePromote = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        setSuccessMessage(null);
        setLoading(true);

        if (!usernameToPromote.trim()) {
            setError("Please enter a username to promote.");
            setLoading(false);
            return;
        }

        try {
            const response = await api.promoteToParent({ username: usernameToPromote });
            setSuccessMessage(`User '${response.data.username}' successfully promoted to Parent.`);
            setUsernameToPromote(''); // Clear input on success
        } catch (err: any) {
            setError(err.response?.data?.detail || `Failed to promote user '${usernameToPromote}'.`);
            console.error("Error promoting user:", err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Paper shadow="xs" p="lg" withBorder>
            <Title order={4} mb="md">Promote User to Parent</Title>
            <form onSubmit={handlePromote}>
                <Stack>
                    <TextInput
                        label="Username to Promote"
                        placeholder="Enter username of the user"
                        value={usernameToPromote}
                        onChange={(event) => setUsernameToPromote(event.currentTarget.value)}
                        required
                    />
                    {error && (
                        <Alert icon={<IconAlertCircle size="1rem" />} title="Promotion Error" color="red" radius="md">
                            {error}
                        </Alert>
                    )}
                    {successMessage && (
                        <Alert title="Success" color="green" radius="md">
                            {successMessage}
                        </Alert>
                    )}
                    <Button
                        type="submit"
                        loading={loading}
                        leftSection={<IconUserUp size={16} />}
                        disabled={!usernameToPromote.trim()}
                    >
                        Promote to Parent
                    </Button>
                </Stack>
            </form>
        </Paper>
    );
};

export default UserManagement;
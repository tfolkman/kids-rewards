import React, { useState, useEffect } from 'react';
import {
    Paper,
    Title,
    Text,
    Button,
    Stack,
    Group,
    Select,
    Table,
    Badge,
    ActionIcon,
    CopyButton,
    Tooltip,
    Alert,
    Card,
    SimpleGrid,
    Divider,
    Modal,
    TextInput
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { 
    IconUserPlus, 
    IconCopy, 
    IconTrash, 
    IconUsers,
    IconCheck,
    IconX,
    IconRefresh
} from '@tabler/icons-react';
import apiClient, * as api from '../services/api';
import { useAuth } from '../App';

interface InvitationInfo {
    code: string;
    role: 'parent' | 'kid';
    expires: string;
    created_by: string;
    created_at: string;
}

interface FamilyMembers {
    family: {
        id: string;
        name: string;
    };
    members: api.User[];
}

const FamilyManagement: React.FC = () => {
    const { currentUser } = useAuth();
    const [invitations, setInvitations] = useState<InvitationInfo[]>([]);
    const [familyMembers, setFamilyMembers] = useState<FamilyMembers | null>(null);
    const [loading, setLoading] = useState(false);
    const [creatingInvite, setCreatingInvite] = useState(false);
    const [selectedRole, setSelectedRole] = useState<'kid' | 'parent'>('kid');
    const [showRemoveModal, setShowRemoveModal] = useState(false);
    const [memberToRemove, setMemberToRemove] = useState<api.User | null>(null);

    const fetchInvitations = async () => {
        try {
            const response = await apiClient.get<InvitationInfo[]>('/families/invitations');
            setInvitations(response.data);
        } catch (error) {
            console.error('Failed to fetch invitations:', error);
        }
    };

    const fetchFamilyMembers = async () => {
        try {
            const response = await apiClient.get<FamilyMembers>('/families/members');
            setFamilyMembers(response.data);
        } catch (error) {
            console.error('Failed to fetch family members:', error);
        }
    };

    useEffect(() => {
        setLoading(true);
        Promise.all([fetchInvitations(), fetchFamilyMembers()])
            .finally(() => setLoading(false));
    }, []);

    const createInvitation = async () => {
        setCreatingInvite(true);
        try {
            const response = await apiClient.post<InvitationInfo>('/families/invitations', {
                role: selectedRole
            });
            
            notifications.show({
                title: 'Invitation Created',
                message: `Invitation code: ${response.data.code}`,
                color: 'teal',
                icon: <IconCheck size={16} />
            });
            
            await fetchInvitations();
        } catch (error: any) {
            notifications.show({
                title: 'Error',
                message: error.response?.data?.detail || 'Failed to create invitation',
                color: 'red',
                icon: <IconX size={16} />
            });
        } finally {
            setCreatingInvite(false);
        }
    };

    const revokeInvitation = async (code: string) => {
        try {
            await apiClient.delete(`/families/invitations/${code}`);
            notifications.show({
                title: 'Invitation Revoked',
                message: 'The invitation has been revoked',
                color: 'teal',
                icon: <IconCheck size={16} />
            });
            await fetchInvitations();
        } catch (error) {
            notifications.show({
                title: 'Error',
                message: 'Failed to revoke invitation',
                color: 'red',
                icon: <IconX size={16} />
            });
        }
    };

    const removeFamilyMember = async () => {
        if (!memberToRemove) return;
        
        try {
            await apiClient.delete(`/families/members/${memberToRemove.username}`);
            notifications.show({
                title: 'Member Removed',
                message: `${memberToRemove.username} has been removed from the family`,
                color: 'teal',
                icon: <IconCheck size={16} />
            });
            setShowRemoveModal(false);
            setMemberToRemove(null);
            await fetchFamilyMembers();
        } catch (error) {
            notifications.show({
                title: 'Error',
                message: 'Failed to remove family member',
                color: 'red',
                icon: <IconX size={16} />
            });
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString();
    };

    const isExpired = (dateString: string) => {
        return new Date(dateString) < new Date();
    };

    return (
        <Stack>
            <Title order={2}>Family Management</Title>
            
            {familyMembers && (
                <Card shadow="sm" padding="lg" radius="md" withBorder>
                    <Group justify="space-between" mb="xs">
                        <Title order={3}>
                            <IconUsers size={24} style={{ marginRight: 8, verticalAlign: 'middle' }} />
                            {familyMembers.family.name} Family
                        </Title>
                        <Badge size="lg" variant="filled">
                            {familyMembers.members.length} {familyMembers.members.length === 1 ? 'Member' : 'Members'}
                        </Badge>
                    </Group>
                </Card>
            )}

            <Paper shadow="sm" p="md" withBorder>
                <Group justify="space-between" mb="md">
                    <Title order={3}>Create Invitation</Title>
                    <Button
                        leftSection={<IconRefresh size={16} />}
                        variant="subtle"
                        onClick={() => fetchInvitations()}
                    >
                        Refresh
                    </Button>
                </Group>
                
                <Group>
                    <Select
                        label="Role for new member"
                        value={selectedRole}
                        onChange={(value) => setSelectedRole(value as 'kid' | 'parent')}
                        data={[
                            { value: 'kid', label: 'Kid' },
                            { value: 'parent', label: 'Parent' }
                        ]}
                        style={{ flex: 1 }}
                    />
                    <Button
                        leftSection={<IconUserPlus size={16} />}
                        onClick={createInvitation}
                        loading={creatingInvite}
                        style={{ marginTop: 24 }}
                    >
                        Create Invitation
                    </Button>
                </Group>
            </Paper>

            {invitations.length > 0 && (
                <Paper shadow="sm" p="md" withBorder>
                    <Title order={3} mb="md">Active Invitations</Title>
                    <Table>
                        <Table.Thead>
                            <Table.Tr>
                                <Table.Th>Code</Table.Th>
                                <Table.Th>Role</Table.Th>
                                <Table.Th>Created</Table.Th>
                                <Table.Th>Expires</Table.Th>
                                <Table.Th>Actions</Table.Th>
                            </Table.Tr>
                        </Table.Thead>
                        <Table.Tbody>
                            {invitations.map((invitation) => (
                                <Table.Tr key={invitation.code}>
                                    <Table.Td>
                                        <Group gap="xs">
                                            <Text fw={600} size="lg" style={{ fontFamily: 'monospace' }}>
                                                {invitation.code}
                                            </Text>
                                            <CopyButton value={invitation.code}>
                                                {({ copied, copy }) => (
                                                    <Tooltip label={copied ? 'Copied' : 'Copy code'}>
                                                        <ActionIcon
                                                            color={copied ? 'teal' : 'gray'}
                                                            onClick={copy}
                                                            size="sm"
                                                        >
                                                            {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                                                        </ActionIcon>
                                                    </Tooltip>
                                                )}
                                            </CopyButton>
                                        </Group>
                                    </Table.Td>
                                    <Table.Td>
                                        <Badge color={invitation.role === 'parent' ? 'blue' : 'green'}>
                                            {invitation.role}
                                        </Badge>
                                    </Table.Td>
                                    <Table.Td>{formatDate(invitation.created_at)}</Table.Td>
                                    <Table.Td>
                                        <Badge color={isExpired(invitation.expires) ? 'red' : 'gray'}>
                                            {formatDate(invitation.expires)}
                                        </Badge>
                                    </Table.Td>
                                    <Table.Td>
                                        <Tooltip label="Revoke invitation">
                                            <ActionIcon
                                                color="red"
                                                onClick={() => revokeInvitation(invitation.code)}
                                            >
                                                <IconTrash size={16} />
                                            </ActionIcon>
                                        </Tooltip>
                                    </Table.Td>
                                </Table.Tr>
                            ))}
                        </Table.Tbody>
                    </Table>
                </Paper>
            )}

            {familyMembers && familyMembers.members.length > 0 && (
                <Paper shadow="sm" p="md" withBorder>
                    <Title order={3} mb="md">Family Members</Title>
                    <Table>
                        <Table.Thead>
                            <Table.Tr>
                                <Table.Th>Username</Table.Th>
                                <Table.Th>Role</Table.Th>
                                <Table.Th>Points</Table.Th>
                                <Table.Th>Actions</Table.Th>
                            </Table.Tr>
                        </Table.Thead>
                        <Table.Tbody>
                            {familyMembers.members.map((member) => (
                                <Table.Tr key={member.id}>
                                    <Table.Td>{member.username}</Table.Td>
                                    <Table.Td>
                                        <Badge color={member.role === 'parent' ? 'blue' : 'green'}>
                                            {member.role}
                                        </Badge>
                                    </Table.Td>
                                    <Table.Td>
                                        {member.role === 'kid' ? member.points || 0 : '-'}
                                    </Table.Td>
                                    <Table.Td>
                                        {member.username !== currentUser?.username && (
                                            <Tooltip label="Remove from family">
                                                <ActionIcon
                                                    color="red"
                                                    onClick={() => {
                                                        setMemberToRemove(member);
                                                        setShowRemoveModal(true);
                                                    }}
                                                >
                                                    <IconTrash size={16} />
                                                </ActionIcon>
                                            </Tooltip>
                                        )}
                                    </Table.Td>
                                </Table.Tr>
                            ))}
                        </Table.Tbody>
                    </Table>
                </Paper>
            )}

            <Modal
                opened={showRemoveModal}
                onClose={() => {
                    setShowRemoveModal(false);
                    setMemberToRemove(null);
                }}
                title="Remove Family Member"
            >
                <Text>
                    Are you sure you want to remove <strong>{memberToRemove?.username}</strong> from the family?
                    This action cannot be undone.
                </Text>
                <Group mt="lg" justify="flex-end">
                    <Button variant="subtle" onClick={() => setShowRemoveModal(false)}>
                        Cancel
                    </Button>
                    <Button color="red" onClick={removeFamilyMember}>
                        Remove Member
                    </Button>
                </Group>
            </Modal>
        </Stack>
    );
};

export default FamilyManagement;
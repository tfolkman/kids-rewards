import React, { useState } from 'react';
import {
  Container,
  Title,
  Select,
  TextInput,
  Textarea,
  NumberInput,
  Button,
  Group,
  Paper,
  LoadingOverlay,
  Alert,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconCircleCheck, IconAlertCircle } from '@tabler/icons-react';
// We will create this API function later
import { submitFeatureRequest, KidFeatureRequestPayloadAPI, RequestTypeAPI as RequestType } from '../services/api'; // Updated import

// Matches backend models.RequestType
// enum RequestType is now imported from '../services/api.ts' and aliased as RequestType.

interface FormValues {
  request_type: RequestType | ''; // Uses the imported enum
  name: string;
  description: string;
  points_value: number | ''; // For chores or store items
  message: string; // For 'other' requests
}

const MakeRequestPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<FormValues>({
    initialValues: {
      request_type: '',
      name: '',
      description: '',
      points_value: '',
      message: '',
    },
    validate: (values) => {
      if (!values.request_type) {
        return { request_type: 'Request type is required' };
      }
      if (values.request_type === RequestType.ADD_STORE_ITEM || values.request_type === RequestType.ADD_CHORE) {
        if (!values.name.trim()) return { name: 'Name is required' };
        if (values.points_value === '' || (typeof values.points_value === 'number' && values.points_value <= 0)) {
          return { points_value: 'Points must be a positive number' };
        }
      }
      if (values.request_type === RequestType.OTHER) {
        if (!values.message.trim()) return { message: 'Message is required' };
      }
      return {};
    },
  });

  const handleSubmit = async (values: FormValues) => {
    setLoading(true);
    setError(null);

    let details: any = {};
    if (values.request_type === RequestType.ADD_STORE_ITEM) {
      details = {
        name: values.name,
        description: values.description,
        points_cost: values.points_value,
      };
    } else if (values.request_type === RequestType.ADD_CHORE) {
      details = {
        name: values.name,
        description: values.description,
        points_value: values.points_value,
      };
    } else if (values.request_type === RequestType.OTHER) {
      details = {
        message: values.message,
      };
    }

    const payload = {
      request_type: values.request_type as RequestType, // Ensure it's not empty string
      details,
    };

    try {
      // TODO: Replace with actual API call
      console.log('Submitting request:', payload);
      await submitFeatureRequest(payload as KidFeatureRequestPayloadAPI); // Use the actual API call and type assertion
      notifications.show({
        title: 'Request Submitted!',
        message: 'Your request has been sent for review.',
        color: 'teal',
        icon: <IconCircleCheck />,
      });
      form.reset();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to submit request.';
      setError(errorMessage);
      notifications.show({
        title: 'Submission Failed',
        message: errorMessage,
        color: 'red',
        icon: <IconAlertCircle />,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container size="sm">
      <Paper withBorder shadow="md" p={30} mt={30} radius="md">
        <Title order={2} ta="center" mb="xl">
          Make a Request
        </Title>
        <LoadingOverlay visible={loading} />
        {error && (
          <Alert title="Error" color="red" withCloseButton onClose={() => setError(null)} mb="md">
            {error}
          </Alert>
        )}
        <form onSubmit={form.onSubmit(handleSubmit)}>
          <Select
            label="Request Type"
            placeholder="Select request type"
            data={[
              { value: RequestType.ADD_STORE_ITEM, label: 'Request New Store Item' },
              { value: RequestType.ADD_CHORE, label: 'Request New Chore' },
              { value: RequestType.OTHER, label: 'Other Request' },
            ]}
            {...form.getInputProps('request_type')}
            mb="md"
            required
          />

          {form.values.request_type === RequestType.ADD_STORE_ITEM && (
            <>
              <TextInput
                label="Item Name"
                placeholder="Enter item name"
                {...form.getInputProps('name')}
                mb="sm"
                required
              />
              <Textarea
                label="Item Description (Optional)"
                placeholder="Enter item description"
                {...form.getInputProps('description')}
                mb="sm"
              />
              <NumberInput
                label="Points Cost"
                placeholder="Enter points cost"
                min={1}
                {...form.getInputProps('points_value')}
                mb="md"
                required
              />
            </>
          )}

          {form.values.request_type === RequestType.ADD_CHORE && (
            <>
              <TextInput
                label="Chore Name"
                placeholder="Enter chore name"
                {...form.getInputProps('name')}
                mb="sm"
                required
              />
              <Textarea
                label="Chore Description (Optional)"
                placeholder="Enter chore description"
                {...form.getInputProps('description')}
                mb="sm"
              />
              <NumberInput
                label="Points Value"
                placeholder="Enter points value"
                min={1}
                {...form.getInputProps('points_value')}
                mb="md"
                required
              />
            </>
          )}

          {form.values.request_type === RequestType.OTHER && (
            <Textarea
              label="Your Request"
              placeholder="Please describe your request"
              {...form.getInputProps('message')}
              minRows={4}
              mb="md"
              required
            />
          )}

          {form.values.request_type && (
            <Group mt="xl" style={{ justifyContent: 'flex-end' }}>
              <Button type="submit" loading={loading}>
                Submit Request
              </Button>
            </Group>
          )}
        </form>
      </Paper>
    </Container>
  );
};

export default MakeRequestPage;
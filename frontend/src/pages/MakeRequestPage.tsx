import React, { useState, useEffect } from 'react';
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
  Modal,
  Text,
  Stack,
  Divider,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconCircleCheck, IconAlertCircle } from '@tabler/icons-react';
// We will create this API function later
import { submitFeatureRequest, KidFeatureRequestPayloadAPI, RequestTypeAPI as RequestType, askGemini } from '../services/api'; // Updated import

// Matches backend models.RequestType
// enum RequestType is now imported from '../services/api.ts' and aliased as RequestType.

interface FormValues {
  request_type: RequestType | ''; // Uses the imported enum
  name: string;
  description: string;
  points_value: number | ''; // For chores or store items
  message: string; // For 'other' requests
}

interface AiChoreDetails {
  name: string;
  description: string;
  timeEstimate: number;
  pointsValue: number;
}

const MakeRequestPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiChoreDetails, setAiChoreDetails] = useState<AiChoreDetails | null>(null);
  const [showChoreConfirmationModal, setShowChoreConfirmationModal] = useState(false);

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

  const submitActualRequest = async (payload: KidFeatureRequestPayloadAPI) => {
    setLoading(true);
    setError(null);
    try {
      console.log('Submitting actual request:', payload);
      await submitFeatureRequest(payload);
      notifications.show({
        title: 'Request Submitted!',
        message: 'Your request has been sent for review.',
        color: 'teal',
        icon: <IconCircleCheck />,
      });
      form.reset();
      setAiChoreDetails(null);
      setShowChoreConfirmationModal(false);
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

  const handleAiChoreConfirmationSubmit = async () => {
    if (!aiChoreDetails) return;

    const payload: KidFeatureRequestPayloadAPI = {
      request_type: RequestType.ADD_CHORE,
      details: {
        name: aiChoreDetails.name,
        description: aiChoreDetails.description,
        points_value: aiChoreDetails.pointsValue,
      },
    };
    setShowChoreConfirmationModal(false);
    await submitActualRequest(payload);
  };


  const handleSubmit = async (values: FormValues) => {
    setLoading(true);
    setError(null);
    setAiChoreDetails(null); // Clear previous AI details

    if (values.request_type === RequestType.OTHER) {
      const geminiPrompt = `You are an assistant helping to process user requests. The user's input is a text message.
Determine if this message is a request to create a new chore.
If it is a chore request:
- Extract or generate a concise name for the chore.
- Extract or generate a brief description for the chore.
- Estimate the time in minutes it would take to complete this chore. If the user provides a time, use that. Otherwise, make a reasonable estimate.
- Respond with a JSON object in the following format:
  {
    "is_chore_request": true,
    "chore_name": "Example Chore Name",
    "chore_description": "Example chore description.",
    "time_estimate_minutes": 30
  }
If the message is NOT a chore request, respond with a JSON object:
  {
    "is_chore_request": false
  }
Ensure your entire response is ONLY the JSON object.`;

      try {
        const response = await askGemini(geminiPrompt, values.message);
        const aiResponse = JSON.parse(response.data.answer);

        if (aiResponse.is_chore_request && aiResponse.chore_name && typeof aiResponse.time_estimate_minutes === 'number') {
          const points = Math.max(1, Math.round(aiResponse.time_estimate_minutes * 3)); // Ensure points are at least 1
          setAiChoreDetails({
            name: aiResponse.chore_name,
            description: aiResponse.chore_description || '',
            timeEstimate: aiResponse.time_estimate_minutes,
            pointsValue: points,
          });
          setShowChoreConfirmationModal(true);
          setLoading(false); // Stop loading as we are waiting for user confirmation
          return; // Don't proceed to submitActualRequest yet
        } else {
          // Not a chore, or AI response is not as expected, submit as general "OTHER" request
          const payload: KidFeatureRequestPayloadAPI = {
            request_type: RequestType.OTHER,
            details: { message: values.message },
          };
          await submitActualRequest(payload);
        }
      } catch (err: any) {
        console.error("Error calling Gemini or parsing response:", err);
        setError("Failed to process AI request. Submitting as a general request.");
        // Fallback to submitting as a general "OTHER" request
        const payload: KidFeatureRequestPayloadAPI = {
          request_type: RequestType.OTHER,
          details: { message: values.message },
        };
        // setLoading(true) is already set, submitActualRequest will handle finally setLoading(false)
        await submitActualRequest(payload);
      }
    } else {
      // Handle ADD_STORE_ITEM and ADD_CHORE directly
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
      }
      const payload: KidFeatureRequestPayloadAPI = {
        request_type: values.request_type as RequestType,
        details,
      };
      await submitActualRequest(payload);
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
              { value: RequestType.OTHER, label: 'AI Assistant Request' },
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

      {aiChoreDetails && (
        <Modal
          opened={showChoreConfirmationModal}
          onClose={() => {
            setShowChoreConfirmationModal(false);
            // Optionally, ask user if they want to submit original message as "OTHER"
            // For now, just closes and user can resubmit if they wish.
          }}
          title={<Title order={4}>Confirm AI Suggested Chore</Title>}
          centered
          size="lg"
        >
          <Stack>
            <Text>The AI assistant processed your request as a new chore with the following details:</Text>
            <Paper withBorder p="md" radius="sm">
              <Text><strong>Chore Name:</strong> {aiChoreDetails.name}</Text>
              <Text><strong>Description:</strong> {aiChoreDetails.description || "N/A"}</Text>
              <Text><strong>Estimated Time:</strong> {aiChoreDetails.timeEstimate} minutes</Text>
              <Text fw={700} c="teal"><strong>Calculated Points:</strong> {aiChoreDetails.pointsValue}</Text>
            </Paper>
            <Text>Would you like to submit this as a new chore request?</Text>
            <Group style={{ justifyContent: 'flex-end' }} mt="md">
              <Button
                variant="outline"
                onClick={() => {
                  setShowChoreConfirmationModal(false);
                  // Submit the original message as a general "OTHER" request
                  const originalPayload: KidFeatureRequestPayloadAPI = {
                    request_type: RequestType.OTHER,
                    details: { message: form.values.message },
                  };
                  submitActualRequest(originalPayload);
                }}
              >
                No, submit original text
              </Button>
              <Button onClick={handleAiChoreConfirmationSubmit} loading={loading}>
                Yes, Submit Chore Request
              </Button>
            </Group>
          </Stack>
        </Modal>
      )}
    </Container>
  );
};

export default MakeRequestPage;
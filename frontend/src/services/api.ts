import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'https://nb8fzkab80.execute-api.us-west-2.amazonaws.com/prod';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Function to get the token from localStorage
const getToken = () => localStorage.getItem('token');

// Add a request interceptor to include the token in headers
apiClient.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Unwrap API envelope: {success, data, meta, error} -> data
apiClient.interceptors.response.use(
  (response) => {
    if (response.data && typeof response.data === 'object' && 'success' in response.data) {
      response.data = response.data.data;
    }
    return response;
  },
  (error) => {
    if (error.response?.data && typeof error.response.data === 'object' && 'error' in error.response.data) {
      const apiError = error.response.data.error;
      error.message = apiError?.message || error.message;
      error.code = apiError?.code;
    }
    return Promise.reject(error);
  }
);

// User types (can be expanded or moved to a dedicated types file)
export interface User {
  id: string;
  username: string;
  role: 'parent' | 'kid';
  points?: number;
}

export interface UserCreate {
  username: string;
  password: string;
  // role is no longer set by the client during creation
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

// Store Item types
export interface StoreItem {
    id: string;
    name: string;
    description?: string;
    points_cost: number;
}

export interface StoreItemCreate {
    name: string;
    description?: string;
    points_cost: number;
}

export interface PointsAwardData {
    kid_username: string;
    points: number;
    reason?: string;
}

export interface RedemptionRequestData {
    item_id: string;
}

export interface UserPromoteData {
    username: string;
}

// Purchase Log types
export type PurchaseStatus = "pending" | "approved" | "rejected" | "completed";

export interface PurchaseLog {
  id: string;
  user_id: string;
  username: string;
  item_id: string;
  item_name: string;
  points_spent: number;
  timestamp: string; // ISO date string
  status: PurchaseStatus;
}
// Chore types
export type ChoreStatus = "available" | "pending_approval" | "approved" | "rejected";

export interface Chore {
  id: string;
  name: string;
  description?: string;
  points_value: number;
  created_by_parent_id: string;
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
  is_active: boolean;
}

export interface ChoreCreate {
  name: string;
  description?: string;
  points_value: number;
}

export interface ChoreLog {
  id: string;
  chore_id: string;
  chore_name: string;
  kid_id: string;
  kid_username: string;
  points_value: number;
  status: ChoreStatus;
  submitted_at: string; // ISO date string
  reviewed_by_parent_id?: string;
  reviewed_at?: string; // ISO date string
  // Effort tracking fields
  effort_minutes?: number;
  retry_count?: number;
  effort_points?: number;
  is_retry?: boolean;
}

export interface ChoreActionRequestData {
  chore_log_id: string;
}

// Chore Assignment types
export interface ChoreAssignmentCreate {
  chore_id: string;
  assigned_to_kid_id: string;
  due_date?: string; // ISO date string
  notes?: string;
}

export interface ChoreAssignment {
  id: string;
  chore_id: string;
  chore_name: string;
  assigned_to_kid_id: string;
  kid_username: string;
  points_value: number;
  due_date?: string; // ISO date string
  notes?: string;
  assignment_status: string; // 'assigned', 'submitted', 'approved', 'rejected'
  created_at: string; // ISO date string
  assigned_by_parent_id: string;
  assigned_by_parent_username: string;
  submitted_at?: string; // ISO date string
  submission_notes?: string;
  reviewed_by_parent_id?: string;
  reviewed_at?: string; // ISO date string
}

export interface ChoreAssignmentActionRequest {
  assignment_id: string;
}

export interface ChoreAssignmentSubmission {
  submission_notes?: string;
}

// Feature Request types (matching backend models and frontend pages)
export enum RequestTypeAPI {
  ADD_STORE_ITEM = "add_store_item",
  ADD_CHORE = "add_chore",
  OTHER = "other",
}

export interface FeatureRequestDetailsAPI {
  name?: string;
  description?: string;
  points_cost?: number;
  points_value?: number;
  message?: string;
}

export interface FeatureRequestAPI {
  id: string;
  requester_id: string;
  requester_username: string;
  request_type: RequestTypeAPI;
  details: FeatureRequestDetailsAPI;
  status: "pending" | "approved" | "rejected";
  created_at: string; // ISO string
  reviewed_by_parent_id?: string;
  reviewed_at?: string; // ISO string
}

export interface KidFeatureRequestPayloadAPI {
  request_type: RequestTypeAPI;
  details: FeatureRequestDetailsAPI;
}


// --- API Service Functions ---

// Auth
export const login = (username: string, password: string) => {
    const data = new URLSearchParams();
    data.append('username', username);
    data.append('password', password);

    return apiClient.post<TokenResponse>('/token', data, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' } // FastAPI's OAuth2PasswordRequestForm expects this
    });
};
export const signup = (data: UserCreate) => apiClient.post<User>('/users/', data);
export const getCurrentUser = () => apiClient.get<User>('/users/me/');
export const promoteToParent = (data: UserPromoteData) => apiClient.post<User>('/users/promote-to-parent', data);

// Store Items
export const getStoreItems = () => apiClient.get<StoreItem[]>('/store/items/');
export const createStoreItem = (data: StoreItemCreate) => apiClient.post<StoreItem>('/store/items/', data);
export const updateStoreItem = (itemId: string, data: StoreItemCreate) => apiClient.put<StoreItem>(`/store/items/${itemId}`, data);
export const deleteStoreItem = (itemId: string) => apiClient.delete(`/store/items/${itemId}`);
export const getStoreItemById = (itemId: string) => apiClient.get<StoreItem>(`/store/items/${itemId}`);


// Points Management
export const awardPoints = (data: PointsAwardData) => apiClient.post<User>('/kids/award-points/', data);
export const redeemItem = (data: RedemptionRequestData) => apiClient.post<PurchaseLog>('/kids/redeem-item/', data); // Changed return type

export const helloWorld = () => apiClient.get<{ message: string }>('/hello');
export const getLeaderboard = () => apiClient.get<User[]>('/leaderboard');

// Purchase History
export const getMyPurchaseHistory = () => apiClient.get<PurchaseLog[]>('/users/me/purchase-history');
export const getBeardedDragonPurchases = () => apiClient.get<PurchaseLog[]>('/kids/bearded-dragon-purchases');

// Purchase Approval (Parent)
export interface PurchaseActionData {
  log_id: string;
}
export const getPendingPurchaseRequests = () => apiClient.get<PurchaseLog[]>('/parent/purchase-requests/pending');
export const approvePurchaseRequest = (data: PurchaseActionData) => apiClient.post<PurchaseLog>('/parent/purchase-requests/approve', data);
export const rejectPurchaseRequest = (data: PurchaseActionData) => apiClient.post<PurchaseLog>('/parent/purchase-requests/reject', data);

// Chores
// Parent - Chore Management
export const createChore = (data: ChoreCreate) => apiClient.post<Chore>('/chores/', data);
export const getMyCreatedChores = () => apiClient.get<Chore[]>('/chores/my-chores/');
export const updateChore = (choreId: string, data: ChoreCreate) => apiClient.put<Chore>(`/chores/${choreId}`, data);
export const deactivateChore = (choreId: string) => apiClient.post<Chore>(`/chores/${choreId}/deactivate`);
export const deleteChore = (choreId: string) => apiClient.delete(`/chores/${choreId}`);

// General Chore Interaction (Kids & Parents)
export const getAvailableChores = () => apiClient.get<Chore[]>('/chores/');
export const getChoreById = (choreId: string) => apiClient.get<Chore>(`/chores/${choreId}`);

// Kid - Chore Submission
export interface ChoreSubmissionData {
  effort_minutes?: number;
}

export const submitChoreCompletion = (choreId: string, data?: ChoreSubmissionData) => 
  apiClient.post<ChoreLog>(`/chores/${choreId}/submit`, data || {});
export const getMyChoreHistory = () => apiClient.get<ChoreLog[]>('/chores/history/me');

// Extended ChoreLog type with streak information
export interface ChoreLogWithStreakBonus extends ChoreLog {
  streak_bonus_points?: number;
  streak_day?: number;
  // Effort tracking fields are inherited from ChoreLog
}

export const getMyDetailedChoreHistory = () => apiClient.get<ChoreLogWithStreakBonus[]>('/chores/history/me/detailed');

// Parent - Chore Submission Approval
export const getPendingChoreSubmissionsForMyChores = () => apiClient.get<ChoreLog[]>('/parent/chore-submissions/pending');
export const approveChoreSubmission = (data: ChoreActionRequestData) => apiClient.post<ChoreLog>('/parent/chore-submissions/approve', data);
export const rejectChoreSubmission = (data: ChoreActionRequestData) => apiClient.post<ChoreLog>('/parent/chore-submissions/reject', data);

// Chore Assignments
export const assignChoreToKid = (data: ChoreAssignmentCreate) => apiClient.post<ChoreAssignment>('/parent/chore-assignments/', data);
export const getMyCreatedAssignments = () => apiClient.get<ChoreAssignment[]>('/parent/chore-assignments/');
export const getMyAssignedChores = () => apiClient.get<ChoreAssignment[]>('/kids/my-assignments/');
export const submitAssignmentCompletion = (assignmentId: string, data: ChoreAssignmentSubmission) => apiClient.post<ChoreAssignment>(`/chore-assignments/${assignmentId}/submit`, data);
export const getPendingAssignmentSubmissions = () => apiClient.get<ChoreAssignment[]>('/parent/assignment-submissions/pending');
export const approveAssignmentSubmission = (data: ChoreAssignmentActionRequest) => apiClient.post<ChoreAssignment>('/parent/assignment-submissions/approve', data);
export const rejectAssignmentSubmission = (data: ChoreAssignmentActionRequest) => apiClient.post<ChoreAssignment>('/parent/assignment-submissions/reject', data);

// Feature Requests
export const submitFeatureRequest = (payload: KidFeatureRequestPayloadAPI) => apiClient.post<FeatureRequestAPI>('/requests/', payload);
export const getMyFeatureRequests = () => apiClient.get<FeatureRequestAPI[]>('/requests/me/');
export const getPendingFeatureRequests = () => apiClient.get<FeatureRequestAPI[]>('/parent/requests/pending/');
export const approveFeatureRequest = (requestId: string) => apiClient.post<FeatureRequestAPI>(`/parent/requests/${requestId}/approve/`);
export const rejectFeatureRequest = (requestId: string) => apiClient.post<FeatureRequestAPI>(`/parent/requests/${requestId}/reject/`);

// Gemini API
export const askGemini = (prompt: string, question: string) => apiClient.post<{ answer: string }>('/gemini/ask', { prompt, question });

// --- Pet Care Types ---

export type PetSpecies = "bearded_dragon";
export type BeardedDragonLifeStage = "baby" | "juvenile" | "sub_adult" | "adult";
export type PetCareTaskStatus = "scheduled" | "assigned" | "pending_approval" | "approved" | "rejected" | "skipped";
export type CareFrequency = "daily" | "weekly";
export type WeightStatus = "healthy" | "underweight" | "overweight";

export interface Pet {
  id: string;
  parent_id: string;
  name: string;
  species: PetSpecies;
  birthday: string; // ISO date string
  photo_url?: string;
  care_notes?: string;
  is_active: boolean;
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
}

export interface PetWithAge extends Pet {
  age_months: number;
  life_stage: BeardedDragonLifeStage;
}

export interface PetCreate {
  name: string;
  species: PetSpecies;
  birthday: string; // ISO date string
  photo_url?: string;
  care_notes?: string;
}

export interface CareRecommendation {
  life_stage: BeardedDragonLifeStage;
  feeding_frequency: string;
  diet_ratio: string;
  healthy_weight_range_grams: [number, number];
  care_tips: string[];
}

export interface PetCareSchedule {
  id: string;
  pet_id: string;
  parent_id: string;
  task_name: string;
  description?: string;
  frequency: CareFrequency;
  points_value: number;
  day_of_week?: number; // 0=Monday, 6=Sunday
  due_by_time?: string; // "HH:MM" format, e.g., "10:00"
  assigned_kid_ids: string[];
  rotation_index: number;
  is_active: boolean;
  created_at: string; // ISO date string
  updated_at: string; // ISO date string
}

export interface PetCareScheduleCreate {
  pet_id: string;
  task_name: string;
  description?: string;
  frequency: CareFrequency;
  points_value: number;
  day_of_week?: number;
  due_by_time?: string; // "HH:MM" format, e.g., "10:00"
  assigned_kid_ids: string[];
}

export interface PetCareTask {
  id: string;
  schedule_id: string;
  pet_id: string;
  pet_name: string;
  task_name: string;
  description?: string;
  points_value: number;
  assigned_to_kid_id: string;
  assigned_to_kid_username: string;
  due_date: string; // ISO date string
  status: PetCareTaskStatus;
  created_at: string; // ISO date string
  submitted_at?: string; // ISO date string
  submission_notes?: string;
  reviewed_by_parent_id?: string;
  reviewed_at?: string; // ISO date string
}

export interface PetCareTaskSubmission {
  notes?: string;
}

export interface PetHealthLog {
  id: string;
  pet_id: string;
  weight_grams: number;
  notes?: string;
  logged_by_user_id: string;
  logged_by_username: string;
  logged_at: string; // ISO date string
  weight_status?: WeightStatus;
  life_stage_at_log?: BeardedDragonLifeStage;
}

export interface PetHealthLogCreate {
  pet_id: string;
  weight_grams: number;
  notes?: string;
}

export interface PetCareTaskActionRequest {
  task_id: string;
}

export interface PetOverviewItem {
  pet: PetWithAge;
  care_recommendations: CareRecommendation;
  latest_weight: PetHealthLog | null;
  pending_tasks: number;
  awaiting_approval: number;
}

export interface PetCareOverview {
  pets: PetOverviewItem[];
}

export interface RecommendedCareSchedule {
  task_name: string;
  task_type: string;
  frequency: CareFrequency;
  points_value: number;
  description: string;
}

// --- Pet Care API Functions ---

// Pets
export const createPet = (data: PetCreate) => apiClient.post<PetWithAge>('/pets/', data);
export const getPets = () => apiClient.get<PetWithAge[]>('/pets/');
export const getPetById = (petId: string) => apiClient.get<PetWithAge>(`/pets/${petId}`);
export const updatePet = (petId: string, data: PetCreate) => apiClient.put<PetWithAge>(`/pets/${petId}`, data);
export const deactivatePet = (petId: string) => apiClient.post<PetWithAge>(`/pets/${petId}/deactivate`);
export const getPetCareRecommendations = (petId: string) => apiClient.get<CareRecommendation>(`/pets/${petId}/care-recommendations`);
export const getRecommendedSchedules = (petId: string) => apiClient.get<RecommendedCareSchedule[]>(`/pets/${petId}/recommended-schedules`);
export const getPetCareOverview = () => apiClient.get<PetCareOverview>('/pets/overview/');

// Pet Care Schedules
export const createPetCareSchedule = (data: PetCareScheduleCreate) => apiClient.post<PetCareSchedule>('/pets/schedules/', data);
export const getPetSchedules = (petId: string) => apiClient.get<PetCareSchedule[]>(`/pets/${petId}/schedules/`);
export const deactivatePetCareSchedule = (scheduleId: string) => apiClient.post<PetCareSchedule>(`/pets/schedules/${scheduleId}/deactivate`);
export const generatePetCareTasks = (scheduleId: string, daysAhead: number = 7) =>
  apiClient.post<PetCareTask[]>(`/pets/schedules/${scheduleId}/generate-tasks?days_ahead=${daysAhead}`);

// Pet Care Tasks
export const getMyPetTasks = () => apiClient.get<PetCareTask[]>('/kids/my-pet-tasks/');
export const getPetTasks = (petId: string) => apiClient.get<PetCareTask[]>(`/pets/${petId}/tasks/`);
export const submitPetCareTask = (taskId: string, data: PetCareTaskSubmission) =>
  apiClient.post<PetCareTask>(`/pets/tasks/${taskId}/submit`, data);
export const getPendingPetTaskSubmissions = () => apiClient.get<PetCareTask[]>('/parent/pet-task-submissions/pending');
export const approvePetCareTask = (data: PetCareTaskActionRequest) =>
  apiClient.post<PetCareTask>('/parent/pet-task-submissions/approve', data);
export const rejectPetCareTask = (data: PetCareTaskActionRequest) =>
  apiClient.post<PetCareTask>('/parent/pet-task-submissions/reject', data);

// Pet Health Logs
export const createPetHealthLog = (petId: string, data: PetHealthLogCreate) =>
  apiClient.post<PetHealthLog>(`/pets/${petId}/health-logs/`, data);
export const getPetHealthLogs = (petId: string) => apiClient.get<PetHealthLog[]>(`/pets/${petId}/health-logs/`);

// Kids Streak
export const getMyStreak = () => apiClient.get<{ current_streak: number; longest_streak: number; last_activity_date: string | null }>('/kids/streak/');

export default apiClient;
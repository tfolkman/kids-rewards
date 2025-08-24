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
export const submitChoreCompletion = (choreId: string) => apiClient.post<ChoreLog>(`/chores/${choreId}/submit`);
export const getMyChoreHistory = () => apiClient.get<ChoreLog[]>('/chores/history/me');

// Extended ChoreLog type with streak information
export interface ChoreLogWithStreakBonus extends ChoreLog {
  streak_bonus_points?: number;
  streak_day?: number;
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

export default apiClient;
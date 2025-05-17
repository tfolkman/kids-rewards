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

// Purchase Approval (Parent)
export interface PurchaseActionData {
  log_id: string;
}
export const getPendingPurchaseRequests = () => apiClient.get<PurchaseLog[]>('/parent/purchase-requests/pending');
export const approvePurchaseRequest = (data: PurchaseActionData) => apiClient.post<PurchaseLog>('/parent/purchase-requests/approve', data);
export const rejectPurchaseRequest = (data: PurchaseActionData) => apiClient.post<PurchaseLog>('/parent/purchase-requests/reject', data);

export default apiClient;
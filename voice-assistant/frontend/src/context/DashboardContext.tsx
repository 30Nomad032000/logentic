import { createContext, useContext, useReducer, type ReactNode } from "react";
import type {
  HealthResponse,
  DashboardStats,
  Conversation,
} from "../api/types";

interface DashboardState {
  health: HealthResponse | null;
  stats: DashboardStats | null;
  conversations: Conversation[];
  conversationsTotal: number;
  selectedConversation: Conversation | null;
  isLoading: boolean;
  error: string | null;
}

type Action =
  | { type: "SET_HEALTH"; payload: HealthResponse }
  | { type: "SET_STATS"; payload: DashboardStats }
  | {
      type: "SET_CONVERSATIONS";
      payload: { conversations: Conversation[]; total: number };
    }
  | { type: "SELECT_CONVERSATION"; payload: Conversation | null }
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "SET_ERROR"; payload: string | null };

const initialState: DashboardState = {
  health: null,
  stats: null,
  conversations: [],
  conversationsTotal: 0,
  selectedConversation: null,
  isLoading: true,
  error: null,
};

function reducer(state: DashboardState, action: Action): DashboardState {
  switch (action.type) {
    case "SET_HEALTH":
      return { ...state, health: action.payload };
    case "SET_STATS":
      return { ...state, stats: action.payload };
    case "SET_CONVERSATIONS":
      return {
        ...state,
        conversations: action.payload.conversations,
        conversationsTotal: action.payload.total,
      };
    case "SELECT_CONVERSATION":
      return { ...state, selectedConversation: action.payload };
    case "SET_LOADING":
      return { ...state, isLoading: action.payload };
    case "SET_ERROR":
      return { ...state, error: action.payload };
  }
}

const DashboardContext = createContext<DashboardState>(initialState);
const DispatchContext = createContext<React.Dispatch<Action>>(() => {});

export function DashboardProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  return (
    <DashboardContext.Provider value={state}>
      <DispatchContext.Provider value={dispatch}>
        {children}
      </DispatchContext.Provider>
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  return useContext(DashboardContext);
}

export function useDashboardDispatch() {
  return useContext(DispatchContext);
}

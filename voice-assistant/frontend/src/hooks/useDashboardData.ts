import { useEffect, useCallback, useRef } from "react";
import { getHealth, getStats, getConversations } from "../api/client";
import { useDashboardDispatch } from "../context/DashboardContext";

const POLL_INTERVAL = 15_000;

export function useDashboardData() {
  const dispatch = useDashboardDispatch();
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

  const refresh = useCallback(async () => {
    try {
      const [health, stats, convData] = await Promise.all([
        getHealth(),
        getStats(),
        getConversations(30, 0),
      ]);

      dispatch({ type: "SET_HEALTH", payload: health });
      dispatch({ type: "SET_STATS", payload: stats });
      dispatch({
        type: "SET_CONVERSATIONS",
        payload: {
          conversations: convData.conversations,
          total: convData.total,
        },
      });
      dispatch({ type: "SET_ERROR", payload: null });
    } catch (e) {
      dispatch({
        type: "SET_ERROR",
        payload: e instanceof Error ? e.message : "Failed to fetch data",
      });
    } finally {
      dispatch({ type: "SET_LOADING", payload: false });
    }
  }, [dispatch]);

  useEffect(() => {
    refresh();
    intervalRef.current = setInterval(refresh, POLL_INTERVAL);
    return () => clearInterval(intervalRef.current);
  }, [refresh]);

  return { refresh };
}

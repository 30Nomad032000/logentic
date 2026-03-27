import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/common/Card";
import { getTasks, updateTaskStatus, deleteTask } from "../../api/client";
import type { TaskItem } from "../../api/types";

export function TaskPanel() {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const data = await getTasks();
      setTasks(data.tasks);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  const toggle = async (task: TaskItem) => {
    const next = task.status === "pending" ? "done" : "pending";
    await updateTaskStatus(task.id, next);
    refresh();
  };

  const remove = async (id: string) => {
    await deleteTask(id);
    refresh();
  };

  const pending = tasks.filter((t) => t.status === "pending");
  const done = tasks.filter((t) => t.status === "done");

  return (
    <Card title="Agent Tasks">
      {loading ? (
        <p className="text-[#6b6560] text-sm">Loading...</p>
      ) : tasks.length === 0 ? (
        <p className="text-[#6b6560] text-sm italic">
          No tasks yet. Try saying "Remind me to buy groceries" in the Try It
          panel.
        </p>
      ) : (
        <div className="space-y-3">
          {pending.length > 0 && (
            <ul className="space-y-2">
              {pending.map((t) => (
                <TaskRow
                  key={t.id}
                  task={t}
                  onToggle={toggle}
                  onDelete={remove}
                />
              ))}
            </ul>
          )}

          {done.length > 0 && (
            <>
              <div className="text-[10px] font-mono font-semibold text-[#6b6560] uppercase tracking-[0.08em] pt-1">
                Completed
              </div>
              <ul className="space-y-2">
                {done.map((t) => (
                  <TaskRow
                    key={t.id}
                    task={t}
                    onToggle={toggle}
                    onDelete={remove}
                  />
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </Card>
  );
}

function TaskRow({
  task,
  onToggle,
  onDelete,
}: {
  task: TaskItem;
  onToggle: (t: TaskItem) => void;
  onDelete: (id: string) => void;
}) {
  const isDone = task.status === "done";
  const time = new Date(task.created_at + "Z").toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <li className="flex items-center gap-3 group">
      <button
        onClick={() => onToggle(task)}
        className={`flex-shrink-0 w-[18px] h-[18px] rounded-[4px] border-2 transition-colors ${
          isDone
            ? "bg-[rgba(46,204,113,0.25)] border-[rgba(46,204,113,0.5)]"
            : "border-[rgba(255,200,120,0.2)] hover:border-[rgba(255,200,120,0.4)]"
        }`}
      >
        {isDone && (
          <svg
            viewBox="0 0 14 14"
            className="w-full h-full text-[#2ecc71]"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M3 7.5l3 3 5-6" />
          </svg>
        )}
      </button>

      <div className="flex-1 min-w-0">
        <span
          className={`text-sm ${
            isDone
              ? "text-[#6b6560] line-through"
              : "text-[#d4cfc9]"
          }`}
        >
          {task.title}
        </span>
        <span className="ml-2 text-[10px] text-[#555049]">{time}</span>
      </div>

      <button
        onClick={() => onDelete(task.id)}
        className="opacity-0 group-hover:opacity-100 text-[#6b6560] hover:text-[#e74c3c] transition-opacity text-xs px-1"
        title="Delete"
      >
        x
      </button>
    </li>
  );
}

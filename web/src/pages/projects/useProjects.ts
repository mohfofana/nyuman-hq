import { useCallback, useEffect, useState } from "react";
import { projectsApi, type PageMeta, type Project, type Task } from "../../lib/api";
import { useLive } from "../../lib/live";

export function useProjectList() {
  const { subscribe } = useLive();
  const [projects, setProjects] = useState<Project[] | null>(null);
  const load = useCallback(() => projectsApi.list().then(setProjects), []);
  useEffect(() => { load(); }, [load]);
  useEffect(() => subscribe((ev) => { if (ev.type === "project.updated" || ev.type === "task.updated") load(); }), [subscribe, load]);
  return { projects, reload: load };
}

export function usePages(projectId: string | undefined) {
  const { subscribe } = useLive();
  const [pages, setPages] = useState<PageMeta[]>([]);
  const load = useCallback(() => { if (projectId) projectsApi.pages(projectId).then(setPages); }, [projectId]);
  useEffect(() => { setPages([]); load(); }, [load]);
  useEffect(() => subscribe((ev) => { if (ev.type === "page.updated" && ev.project_id === projectId) load(); }), [subscribe, load, projectId]);
  return { pages, reload: load };
}

/** Tâches filtrées, tenues à jour en direct (mise à jour locale immédiate). */
export function useTasks(params: Record<string, string> | null) {
  const { subscribe } = useLive();
  const [tasks, setTasks] = useState<Task[] | null>(null);
  const key = params ? JSON.stringify(params) : "";
  const load = useCallback(() => { if (params) projectsApi.tasks(params).then(setTasks); }, [key]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { setTasks(null); load(); }, [load]);
  useEffect(() => subscribe((ev) => { if (ev.type === "task.updated") load(); }), [subscribe, load]);
  const patch = useCallback(async (id: string, d: Partial<Task>) => {
    setTasks((l) => l?.map((t) => (t.id === id ? { ...t, ...d } : t)) ?? l);
    await projectsApi.updateTask(id, d);
  }, []);
  return { tasks, reload: load, patch };
}

/** Клиент API «Сроков» — единственное место, знающее о контракте (docs/PLAN.md, раздел 3). */

export type Kind = "study" | "work" | "other";
export type Status = "todo" | "in_progress" | "done";
export type Priority = 1 | 2 | 3;

export interface Category {
  id: number;
  name: string;
  kind: Kind;
  color: string;
  created_at: string;
  open_count: number;
}

export interface Deadline {
  id: number;
  title: string;
  description: string;
  due_at: string; // 'YYYY-MM-DDTHH:MM'
  category_id: number | null;
  priority: Priority;
  status: Status;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  is_overdue: boolean;
}

export interface Stats {
  overdue: number;
  today: number;
  week: number;
  open: number;
  done: number;
}

export interface CategoryInput {
  name: string;
  kind: Kind;
  color?: string;
}

export interface DeadlineInput {
  title: string;
  due_at: string;
  description?: string;
  category_id?: number | null;
  priority?: Priority;
  status?: Status;
}

export interface DeadlineFilters {
  status?: Status | "open";
  category_id?: number | "none" | "";
  q?: string;
  from?: string;
  to?: string;
  sort?: "due" | "priority" | "created";
}

export class ApiError extends Error {
  /** status: HTTP-код (0 — нет связи); field: имя невалидного поля, если сервер его указал. */
  constructor(
    public status: number,
    message: string,
    public field: string | null = null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const BASE = "/api";

/** Query-строка без пустых значений. */
export function query(params: object = {}): string {
  const qs = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") qs.set(key, String(value));
  }
  const s = qs.toString();
  return s ? `?${s}` : "";
}

async function request<T>(method: string, path: string, body?: unknown, params?: object): Promise<T> {
  const init: RequestInit = { method, headers: { Accept: "application/json" } };
  if (body !== undefined) {
    init.headers = { ...init.headers, "Content-Type": "application/json; charset=utf-8" };
    init.body = JSON.stringify(body);
  }
  let res: Response;
  try {
    res = await fetch(BASE + path + query(params), init);
  } catch {
    throw new ApiError(0, "Нет связи с сервером. Проверьте, что он запущен, и повторите.");
  }
  if (res.status === 204) return undefined as T;
  const data = await res.json().catch(() => null);
  if (res.ok) return data as T;
  if (res.status === 413) throw new ApiError(413, "Слишком много текста: сократите заметки и сохраните снова.");
  if (res.status >= 500) throw new ApiError(res.status, "Сервер не смог выполнить запрос. Повторите чуть позже.");
  const field = data?.field ?? (res.status === 409 ? "name" : null); // 409 — дубль имени категории
  throw new ApiError(res.status, data?.error || `Сервер ответил ошибкой ${res.status}.`, field);
}

export const api = {
  listCategories: () => request<Category[]>("GET", "/categories"),
  createCategory: (data: CategoryInput) => request<Category>("POST", "/categories", data),
  updateCategory: (id: number, patch: Partial<CategoryInput>) => request<Category>("PATCH", `/categories/${id}`, patch),
  deleteCategory: (id: number) => request<void>("DELETE", `/categories/${id}`),

  listDeadlines: (filters: DeadlineFilters = {}) => request<Deadline[]>("GET", "/deadlines", undefined, filters),
  createDeadline: (data: DeadlineInput) => request<Deadline>("POST", "/deadlines", data),
  updateDeadline: (id: number, patch: Partial<DeadlineInput>) => request<Deadline>("PATCH", `/deadlines/${id}`, patch),
  deleteDeadline: (id: number) => request<void>("DELETE", `/deadlines/${id}`),

  stats: () => request<Stats>("GET", "/stats"),

  /** Ссылка на .ics с теми же фильтрами, что у календаря. */
  exportUrl: (filters: DeadlineFilters = {}) => `${BASE}/export.ics${query(filters)}`,
};

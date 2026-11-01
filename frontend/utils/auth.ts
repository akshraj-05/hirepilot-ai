export type AuthUser = {
  id: string;
  email: string;
  name: string | null;
  role: string | null;
  organization_id: string;
};

export function setUser(user: AuthUser): void {
  localStorage.setItem("hp_user", JSON.stringify(user));
  document.cookie = "hp_auth=1; path=/; SameSite=Lax";
}

export function getUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("hp_user");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthUser;
  } catch {
    return null;
  }
}

export function getOrgId(): string {
  return getUser()?.organization_id ?? "";
}

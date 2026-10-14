// SPDX-License-Identifier: Apache-2.0
// Hand-written until drf-spectacular + openapi-typescript codegen (roadmap rc-02).

export type Role = "viewer" | "operator" | "admin";

export interface CurrentUser {
  username: string;
  roles: Role[];
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiErrorBody {
  error: { code: string; message: string; details: unknown };
}

export interface Organization {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Tenant {
  id: number;
  organization: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Region {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Site {
  id: number;
  name: string;
  region: number | null;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface ReferenceRecord {
  id: number;
  name: string;
  description: string;
}

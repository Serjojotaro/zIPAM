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

export type PrefixStatus = "active" | "reserved" | "container" | "deprecated";
export type IpStatus = "active" | "reserved" | "deprecated";

export interface Vrf {
  id: number;
  name: string;
  rd: string;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Vlan {
  id: number;
  name: string;
  vid: number;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Prefix {
  id: number;
  vrf: number;
  prefix: string;
  status: PrefixStatus;
  tenant: number | null;
  site: number | null;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface IPAddress {
  id: number;
  vrf: number;
  address: string;
  status: IpStatus;
  description: string;
  created_at: string;
  updated_at: string;
}

export interface Utilization {
  total: number;
  allocated: number;
  available: number;
  utilization_percent: number;
}

export interface AvailableSubnetsResponse {
  prefix: string;
  available_subnets: string[];
}

export interface SearchResultGroup {
  id: number;
  name?: string;
  prefix?: string;
  address?: string;
  status?: IpStatus;
  vid?: number;
  vrf?: number;
}

export interface SearchResponse {
  query: string;
  results: {
    ip_addresses: SearchResultGroup[];
    prefixes: SearchResultGroup[];
    vrfs: SearchResultGroup[];
    vlans: SearchResultGroup[];
    organizations: SearchResultGroup[];
    tenants: SearchResultGroup[];
    regions: SearchResultGroup[];
    sites: SearchResultGroup[];
  };
}

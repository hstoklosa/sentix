import { InternalAxiosRequestConfig } from "axios";

export type RetryableRequestConfig = {
  _retry?: boolean;
} & InternalAxiosRequestConfig;

export type BaseEntity = {
  id: number;
  created_at: string;
  updated_at: string;
};

export type Entity<T> = {
  [K in keyof T]: T[K];
} & BaseEntity;

export type PaginationParams = {
  page: number;
  page_size: number;
};

export type PaginatedResponse<T> = {
  items: T[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
};

export type User = Entity<{
  username: string;
  email: string;
  is_superuser: boolean;
}>;

export type AuthResponse = {
  token: {
    access_token: string;
    token_type: string;
  };
  user: User;
};

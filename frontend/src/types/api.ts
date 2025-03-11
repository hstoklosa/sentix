export type BaseEntity = {
  id: number;
  created_at: string;
  updated_at: string;
};

export type Entity<T> = {
  [K in keyof T]: T[K];
} & BaseEntity;

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

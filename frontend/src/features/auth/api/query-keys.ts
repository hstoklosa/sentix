export const userQueryKeys = {
  all: ["user"] as const,
  details: (id: string) => [...userQueryKeys.all, id] as const,
} as const;

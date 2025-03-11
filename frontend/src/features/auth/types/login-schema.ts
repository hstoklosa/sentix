import { z } from "zod";

/**
 * Schema for the login form
 * Validates user input for login
 */
export const loginFormSchema = z.object({
  username: z.string().min(1, {
    message: "Username is required.",
  }),
  password: z.string().min(1, {
    message: "Password is required.",
  }),
});

/**
 * Type definition for the login form values
 * Inferred from the Zod schema
 */
export type LoginFormValues = z.infer<typeof loginFormSchema>;

import { z } from "zod";

/**
 * Schema for the registration form
 * Validates user input for registration
 */
export const registerFormSchema = z
  .object({
    username: z.string().min(3, {
      message: "Username must be at least 3 characters.",
    }),
    email: z.string().email({
      message: "Please enter a valid email address.",
    }),
    password: z.string().min(8, {
      message: "Password must be at least 8 characters.",
    }),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match.",
    path: ["confirmPassword"],
  });

/**
 * Type definition for the registration form values
 * Inferred from the Zod schema
 */
export type RegisterFormValues = z.infer<typeof registerFormSchema>;

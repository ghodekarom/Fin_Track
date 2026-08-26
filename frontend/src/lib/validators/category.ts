import { z } from "zod";

export const categorySchema = z.object({
  name: z
    .string()
    .min(1, "Category name is required")
    .max(50, "Category name must be 50 characters or less")
    .refine((val) => val.trim().length > 0, "Category name cannot be empty or whitespace only"),
});

export type CategoryFormValues = z.infer<typeof categorySchema>;

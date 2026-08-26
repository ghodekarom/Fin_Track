import { z } from "zod";

export const expenseSchema = z.object({
  title: z
    .string()
    .min(1, "Title is required")
    .max(50, "Title must be 50 characters or less")
    .refine((val) => val.trim().length > 0, "Title cannot be empty or whitespace only"),
  category_id: z
    .string()
    .uuid("Please select a valid category"),
  amount: z
    .union([z.number(), z.string()])
    .transform((val) => {
      if (typeof val === "number") return val;
      const parsed = parseFloat(val);
      return isNaN(parsed) ? 0 : parsed;
    })
    .refine((val) => val > 0, "Amount must be a positive number"),
  expense_date: z
    .string()
    .min(1, "Date is required")
    .refine((val) => {
      const selectedDate = new Date(val);
      // Remove time components for strict date comparison
      const today = new Date();
      today.setHours(23, 59, 59, 999); // allow today's date regardless of time zones
      return selectedDate <= today;
    }, "Date cannot be in the future"),
  notes: z
    .string()
    .max(250, "Notes must be 250 characters or less")
    .optional()
    .nullable()
    .or(z.literal("")),
  payment_mode: z
    .enum(["cash", "card", "upi", "other"])
    .optional()
    .nullable()
    .or(z.literal("")),
});

export type ExpenseFormValues = z.infer<typeof expenseSchema>;

import { z } from "zod";

export const budgetSchema = z
  .object({
    scope: z.enum(["overall", "category"]),
    category_id: z
      .string()
      .optional()
      .nullable()
      .or(z.literal("")),
    period_month: z
      .string()
      .min(1, "Month is required"),
    limit_amount: z
      .union([z.number(), z.string()])
      .transform((val) => {
        if (typeof val === "number") return val;
        const parsed = parseFloat(val);
        return isNaN(parsed) ? 0 : parsed;
      })
      .refine((val) => val > 0, "Limit must be a positive number"),
  })
  .refine(
    (data) => {
      if (data.scope === "category" && !data.category_id) {
        return false;
      }
      return true;
    },
    {
      message: "Please select a category for a category-scoped budget",
      path: ["category_id"],
    }
  );

export type BudgetFormValues = z.infer<typeof budgetSchema>;

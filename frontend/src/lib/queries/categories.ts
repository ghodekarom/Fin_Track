import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api-client";
import { Category } from "../../types/category";

export const CATEGORIES_QUERY_KEY = ["categories"];

// Fetch all categories
export function useCategories() {
  return useQuery<Category[], any>({
    queryKey: CATEGORIES_QUERY_KEY,
    queryFn: async () => {
      const response = await apiClient.get<Category[]>("/categories");
      return response.data;
    },
  });
}

// Create a category
export function useCreateCategory() {
  const queryClient = useQueryClient();
  
  return useMutation<Category, any, { name: string }>({
    mutationFn: async (payload) => {
      const response = await apiClient.post<Category>("/categories", payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CATEGORIES_QUERY_KEY });
    },
  });
}

// Rename a category
export function useRenameCategory() {
  const queryClient = useQueryClient();
  
  return useMutation<Category, any, { id: string; name: string }>({
    mutationFn: async ({ id, name }) => {
      const response = await apiClient.put<Category>(`/categories/${id}`, { name });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CATEGORIES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}

// Delete a category
interface DeleteCategoryParams {
  id: string;
  reassign_to?: string | null;
  force?: boolean;
}

export function useDeleteCategory() {
  const queryClient = useQueryClient();
  
  return useMutation<void, any, DeleteCategoryParams>({
    mutationFn: async ({ id, reassign_to, force = false }) => {
      const params: Record<string, any> = { force };
      if (reassign_to) {
        params.reassign_to = reassign_to;
      }
      await apiClient.delete(`/categories/${id}`, { params });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: CATEGORIES_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: ["expenses"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["budgets"] });
    },
  });
}

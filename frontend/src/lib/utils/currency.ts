/**
 * Formats a numeric value or numeric string to Indian Rupee (INR) currency style.
 * Example: 1234.56 -> ₹1,234.56
 */
export function formatCurrency(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined) {
    return "₹0.00";
  }
  
  const numericAmount = typeof amount === "string" ? parseFloat(amount) : amount;
  
  if (isNaN(numericAmount)) {
    return "₹0.00";
  }
  
  // Format as Indian Currency grouping format: e.g. 1,00,000.00 instead of 100,000.00
  // Note: we can use Intl.NumberFormat for "en-IN" locale
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(numericAmount);
}

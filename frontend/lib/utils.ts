export function formatCurrency(amountPaise: number, currency: string = "INR") {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amountPaise / 100);
}

export function formatMoney(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(num)) return "-";
  return num.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

export function formatPct(value: string | number): string {
  const num = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(num)) return "0%";
  return `${num.toFixed(0)}%`;
}

export function formatDate(value: string | null): string {
  if (!value) return "-";
  return value;
}

export function today(): string {
  return new Date().toISOString().slice(0, 10);
}

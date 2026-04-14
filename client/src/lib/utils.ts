import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDisplayName(name: string) {
  if (!name) return '';

  let decoded = name;
  try {
    const txt = document.createElement('textarea');
    txt.innerHTML = name;
    decoded = txt.value;
  } catch (e) {
    decoded = name;
  }

  let cleanName = decoded.replace(/[-_./\\]+/g, ' ');
  cleanName = cleanName.replace(/\s+/g, ' ').trim();
  return cleanName.toLowerCase().replace(/\b\w/g, (char) => char.toUpperCase());
}

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
  cleanName = cleanName.replace(/\s*\|\s*/g, ' | ');
  cleanName = cleanName.replace(/\s+/g, ' ').trim();
  return cleanName
    .split(/(\s+|\|)/)
    .map(formatDisplayToken)
    .join('')
    .replace(/\s+\|\s+/g, ' | ');
}

const DISPLAY_TOKEN_CASE: Record<string, string> = {
  ipad: 'iPad',
  iphone: 'iPhone',
  macbook: 'MacBook',
  imac: 'iMac',
  airpods: 'AirPods',
  wifi: 'Wifi',
  inch: 'inch',
  apple: 'Apple',
  samsung: 'Samsung',
  xiaomi: 'Xiaomi',
  poco: 'POCO',
  sony: 'Sony',
  pro: 'Pro',
  max: 'Max',
  mini: 'Mini',
  ultra: 'Ultra',
  plus: 'Plus',
  air: 'Air',
};

function formatDisplayToken(token: string) {
  if (!token.trim() || token === '|') return token;

  const lower = token.toLocaleLowerCase('vi-VN');
  const mapped = DISPLAY_TOKEN_CASE[lower];
  if (mapped) return mapped;

  const storage = lower.match(/^(\d+)(tb|gb|mb)$/i);
  if (storage) return `${storage[1]}${storage[2].toLocaleUpperCase('en-US')}`;

  const model = lower.match(/^([a-z])(\d+[a-z0-9]*)$/i);
  if (model) return `${model[1].toLocaleUpperCase('en-US')}${model[2].toLocaleUpperCase('en-US')}`;

  const chars = Array.from(lower);
  if (chars.length === 0) return token;
  return `${chars[0].toLocaleUpperCase('vi-VN')}${chars.slice(1).join('')}`;
}

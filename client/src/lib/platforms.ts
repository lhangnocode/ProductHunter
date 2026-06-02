export type PlatformDisplaySource = {
  platform_id?: number | null;
  url?: string | null;
  affiliate_url?: string | null;
};

export const PLATFORM_IDS = {
  FPT_SHOP: 7,
  PHONG_VU: 8,
  CELLPHONES: 9,
} as const;

const PLATFORM_META: Record<number, { name: string; gradient: string; badgeClass: string }> = {
  [PLATFORM_IDS.FPT_SHOP]: {
    name: 'FPT Shop',
    gradient: 'from-[#ee4d2d] to-[#d63f1f]',
    badgeClass: 'bg-[#ee4d2d] text-white',
  },
  [PLATFORM_IDS.PHONG_VU]: {
    name: 'Phong Vũ',
    gradient: 'from-[#003da5] to-[#001f5c]',
    badgeClass: 'bg-[#0f136d] text-white',
  },
  [PLATFORM_IDS.CELLPHONES]: {
    name: 'CellphoneS',
    gradient: 'from-[#d70018] to-[#9f0012]',
    badgeClass: 'bg-[#d70018] text-white',
  },
};

const isCellphoneSUrl = (source?: PlatformDisplaySource | null) => {
  const value = `${source?.url || ''} ${source?.affiliate_url || ''}`.toLowerCase();
  return value.includes('cellphones.com.vn') || value.includes('cellphones');
};

export const getPlatformName = (
  id: number | null | undefined,
  source?: PlatformDisplaySource | null,
) => {
  if (id != null && PLATFORM_META[id]) return PLATFORM_META[id].name;
  if (isCellphoneSUrl(source)) return 'CellphoneS';
  return 'Sàn khác';
};

export const getPlatformGradient = (
  id: number | null | undefined,
  source?: PlatformDisplaySource | null,
) => {
  if (id != null && PLATFORM_META[id]) return PLATFORM_META[id].gradient;
  if (isCellphoneSUrl(source)) return PLATFORM_META[PLATFORM_IDS.CELLPHONES].gradient;
  return 'from-[#003da5] to-[#001f5c]';
};

export const getPlatformBadgeClass = (
  id: number | null | undefined,
  source?: PlatformDisplaySource | null,
) => {
  if (id != null && PLATFORM_META[id]) return PLATFORM_META[id].badgeClass;
  if (isCellphoneSUrl(source)) return PLATFORM_META[PLATFORM_IDS.CELLPHONES].badgeClass;
  return 'bg-slate-800 text-white';
};

import { AlertTriangle, Crown, X } from 'lucide-react';
import { motion } from 'motion/react';
import { FREE_PLAN_PRICE_ALERT_LIMIT } from '../context/UserContext';

interface AlertLimitModalProps {
  isOpen: boolean;
  used: number;
  onClose: () => void;
  onUpgrade: () => void;
}

export function AlertLimitModal({ isOpen, used, onClose, onUpgrade }: AlertLimitModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-sm" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, y: 18, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        className="relative w-full max-w-md rounded-[2rem] bg-white p-8 shadow-2xl ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800"
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full p-2 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800"
        >
          <X size={18} />
        </button>

        <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-amber-100 text-amber-600 dark:bg-amber-950/40 dark:text-amber-300">
          <AlertTriangle size={28} />
        </div>

        <h2 className="font-display text-2xl font-black uppercase tracking-tight text-slate-950 dark:text-white">
          Đã đạt giới hạn cảnh báo
        </h2>
        <p className="mt-3 text-sm font-medium leading-6 text-slate-500 dark:text-slate-400">
          Gói Free chỉ cho phép tạo tối đa {FREE_PLAN_PRICE_ALERT_LIMIT} cảnh báo giá. Bạn đang dùng{' '}
          <strong className="text-slate-900 dark:text-white">{Math.min(used, FREE_PLAN_PRICE_ALERT_LIMIT)}/{FREE_PLAN_PRICE_ALERT_LIMIT}</strong>{' '}
          cảnh báo.
        </p>

        <div className="mt-6 rounded-2xl bg-slate-50 p-4 ring-1 ring-inset ring-slate-200 dark:bg-slate-950/40 dark:ring-slate-800">
          <div className="mb-2 flex items-center justify-between text-[10px] font-black uppercase tracking-widest text-slate-500">
            <span>Đã sử dụng</span>
            <span>{Math.min(used, FREE_PLAN_PRICE_ALERT_LIMIT)}/{FREE_PLAN_PRICE_ALERT_LIMIT}</span>
          </div>
          <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-800">
            <div className="h-full rounded-full bg-brand-primary" style={{ width: '100%' }} />
          </div>
        </div>

        <div className="mt-8 flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 rounded-xl bg-slate-100 px-4 py-3 text-xs font-black uppercase tracking-widest text-slate-600 transition-colors hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
          >
            Để sau
          </button>
          <button
            onClick={onUpgrade}
            className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-brand-primary px-4 py-3 text-xs font-black uppercase tracking-widest text-white shadow-lg shadow-brand-primary/20 transition-all hover:-translate-y-0.5"
          >
            <Crown size={15} />
            Nâng cấp Pro
          </button>
        </div>
      </motion.div>
    </div>
  );
}

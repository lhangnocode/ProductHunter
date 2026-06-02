import { Crown, X } from 'lucide-react';
import { motion } from 'motion/react';
import proUpgradeQr from '../assets/pro-upgrade-qr.svg';

interface UpgradeProModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function UpgradeProModal({ isOpen, onClose }: UpgradeProModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[115] flex items-center justify-center p-4">
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

        <div className="mb-5 flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-primary/10 text-brand-primary">
            <Crown size={24} />
          </div>
          <div>
            <p className="text-[9px] font-black uppercase tracking-[0.25em] text-brand-primary">ProductHunter Pro</p>
            <h2 className="font-display text-2xl font-black uppercase tracking-tight text-slate-950 dark:text-white">
              Nâng cấp tài khoản
            </h2>
          </div>
        </div>

        <div className="rounded-3xl bg-slate-50 p-5 ring-1 ring-inset ring-slate-200 dark:bg-slate-950/40 dark:ring-slate-800">
          <img
            src={proUpgradeQr}
            alt="QR chuyển khoản nâng cấp Pro"
            className="mx-auto h-56 w-56 rounded-2xl bg-white object-contain p-2 shadow-sm"
          />
        </div>

        <p className="mt-5 text-sm font-medium leading-6 text-slate-500 dark:text-slate-400">
          Quét mã QR để chuyển khoản nâng cấp Pro. Sau khi thanh toán, admin sẽ xác minh thủ công và cập nhật gói tài khoản của bạn.
        </p>

        <button
          onClick={onClose}
          className="mt-7 w-full rounded-xl bg-brand-primary py-4 text-xs font-black uppercase tracking-widest text-white shadow-xl shadow-brand-primary/20 transition-all hover:opacity-90 active:scale-95"
        >
          Tôi đã hiểu
        </button>
      </motion.div>
    </div>
  );
}

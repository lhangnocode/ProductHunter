import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  X, 
  Download, 
  Settings, 
  Zap, 
  FolderOpen, 
  CheckCircle2,
  ExternalLink 
} from "lucide-react";

interface StepProps {
  number: string;
  title: string;
  desc: string;
  icon: React.ReactNode;
}

const Step = ({ number, title, desc, icon }: StepProps) => (
  <div className="flex gap-4 p-4 rounded-2xl bg-slate-50 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700">
    <div className="flex-none flex h-10 w-10 items-center justify-center rounded-xl bg-brand-primary text-white font-black shadow-lg shadow-brand-primary/20">
      {icon}
    </div>
    <div>
      <div className="flex items-center gap-2">
        <span className="text-[10px] font-black text-brand-primary uppercase tracking-widest">Bước {number}</span>
      </div>
      <h4 className="text-sm font-bold text-slate-900 dark:text-white uppercase">{title}</h4>
      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-relaxed">{desc}</p>
    </div>
  </div>
);

export const ExtensionGuideModal = ({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            className="relative w-full max-w-2xl overflow-hidden rounded-[2.5rem] bg-white dark:bg-slate-900 shadow-2xl ring-1 ring-slate-200 dark:ring-slate-800"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 px-8 py-6">
              <div>
                <h2 className="text-2xl font-black tracking-tight text-slate-950 dark:text-white font-display uppercase">
                  Cài đặt <span className="text-brand-primary">Extension</span>
                </h2>
                <p className="text-xs font-medium text-slate-500">Tiết kiệm hơn khi mua sắm trực tuyến</p>
              </div>
              <button onClick={onClose} className="rounded-full p-2 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                <X size={20} className="text-slate-400" />
              </button>
            </div>

            {/* Content */}
            <div className="max-h-[70vh] overflow-y-auto px-8 py-8">
              <div className="grid gap-4">
                <Step 
                  number="1" 
                  title="Tải & Giải nén" 
                  desc="Tải bản zip từ liên kết cung cấp và giải nén thư mục trên máy tính của bạn." 
                  icon={<Download size={18} />} 
                />
                <Step 
                  number="2" 
                  title="Truy cập Extension" 
                  desc="Mở trình duyệt Chrome và truy cập địa chỉ chrome://extensions/" 
                  icon={<Settings size={18} />} 
                />
                <Step 
                  number="3" 
                  title="Chế độ nhà phát triển" 
                  desc="Bật nút 'Developer mode' ở góc trên bên phải màn hình." 
                  icon={<Zap size={18} />} 
                />
                <Step 
                  number="4" 
                  title="Tải Extension lên" 
                  desc="Bấm 'Load unpacked' và chọn thư mục bạn đã giải nén ở bước 1." 
                  icon={<FolderOpen size={18} />} 
                />
                <div className="p-4 rounded-2xl bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-100 dark:border-emerald-500/20">
                  <div className="flex items-center gap-3 text-emerald-600 dark:text-emerald-400">
                    <CheckCircle2 size={20} />
                    <span className="text-sm font-black uppercase tracking-wider font-display">Sẵn sàng sử dụng!</span>
                  </div>
                  <p className="text-xs text-emerald-600/80 dark:text-emerald-400/80 mt-2">
                    Bây giờ, khi bạn truy cập Shopee, Lazada, Tiki... nút <b>'So sánh giá'</b> sẽ tự động xuất hiện.
                  </p>
                </div>
              </div>

              <div className="mt-8 flex justify-center">
                <a 
                    href="/chrome-mv3-prod.zip" 
                    download
                    className="inline-flex items-center gap-2 rounded-xl bg-brand-primary px-8 py-4 text-sm font-black text-white shadow-xl shadow-brand-primary/20 transition-all hover:scale-105 active:scale-95 uppercase tracking-widest font-display"
                >
                  <Download size={18} />
                  Tải Extension Ngay (.zip)
                </a>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
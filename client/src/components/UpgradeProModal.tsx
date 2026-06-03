import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Check, CreditCard, Upload, Loader2, Sparkles } from 'lucide-react';
import { useUser } from '../context/UserContext';
import { useToast } from './Toast';
import { paymentService } from '../services/payment';


interface UpgradeProModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function UpgradeProModal({ isOpen, onClose }: UpgradeProModalProps) {
  const { user } = useUser();
  const { showToast } = useToast();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const PAYMENT_CONFIG = {
    bankId: "bidv",            
    accountNo: "887038006",       
    accountName: "DANG DINH KHANG",
    bankName: "Ngân hàng BIDV",
    amount: 59000,
  };

  const userContext = useUser(); 

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async () => {
    const token = localStorage.getItem('token'); 

    if (!token) return showToast("Vui lòng đăng nhập", "error");
    if (!selectedFile) return showToast("Vui lòng đính kèm ảnh xác nhận chuyển khoản", "info");

    setIsLoading(true);
    try {
      // Giả sử API đã sẵn sàng, nếu chưa có API thật bạn có thể comment dòng này để test UI
      await paymentService.createPaymentRequest(token, PAYMENT_CONFIG.amount, selectedFile);
      showToast("Gửi yêu cầu thành công! Admin sẽ duyệt sớm nhất có thể.", "success");
      onClose();
    } catch (error: any) {
      showToast(error.message, "error");
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[40] flex items-center justify-center p-4">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose} className="absolute inset-0 bg-slate-900/60 backdrop-blur-md" />
        
        <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
          className="relative w-full max-w-2xl overflow-hidden rounded-[2.5rem] bg-white dark:bg-slate-900 shadow-2xl border border-slate-200 dark:border-slate-800"
        >
          <div className="grid grid-cols-1 md:grid-cols-2">
            {/* Cột 1: Thông tin thanh toán */}
            <div className="p-8 bg-slate-50 dark:bg-slate-950/50">
              <h2 className="text-2xl font-black font-display uppercase text-brand-primary mb-6 flex items-center gap-2">
                <Sparkles /> Gói PRO
              </h2>
              
              <div className="space-y-4 mb-8">
                {['Không giới hạn Alert', 'Ưu tiên săn deal hot', 'Không quảng cáo', 'Hỗ trợ 24/7'].map(item => (
                  <div key={item} className="flex items-center gap-2 text-sm font-bold text-slate-600 dark:text-slate-400">
                    <div className="bg-emerald-500/10 text-emerald-500 rounded-full p-1"><Check size={12} strokeWidth={4} /></div>
                    {item}
                  </div>
                ))}
              </div>

              <div className="rounded-2xl bg-white dark:bg-slate-900 p-6 shadow-sm border border-slate-200 dark:border-slate-800">
                <p className="text-[10px] font-black uppercase text-slate-400 mb-2">Thông tin tài khoản</p>
                
                {/* Dùng biến ở đây */}
                <p className="text-sm font-black text-slate-900 dark:text-white">
                    {PAYMENT_CONFIG.accountName}
                </p>
                <p className="text-lg font-mono font-black text-brand-primary">
                    {PAYMENT_CONFIG.accountNo}
                </p>
                <p className="text-sm font-bold text-slate-500">
                    {PAYMENT_CONFIG.bankName}
                </p>

                <div className="mt-4 pt-4 border-t border-dashed border-slate-200 dark:border-slate-800">
                    <p className="text-xs text-slate-500">Số tiền cần chuyển:</p>
                    <p className="text-xl font-black text-slate-950 dark:text-white">
                    {new Intl.NumberFormat('vi-VN').format(PAYMENT_CONFIG.amount)}đ
                    </p>
                </div>
                </div>


            </div>

            {/* Cột 2: Upload */}
            <div className="p-8 bg-white dark:bg-slate-900">
              <button onClick={onClose} className="absolute right-6 top-6 text-slate-400 hover:text-slate-600"><X size={20}/></button>
              
              <p className="text-sm font-bold text-slate-900 dark:text-white mb-4">Quét mã QR để thanh toán:</p>
              <div className="aspect-square bg-slate-100 dark:bg-slate-800 rounded-2xl mb-6 flex items-center justify-center overflow-hidden border-2 border-slate-100 dark:border-slate-800">
                <img 
                    src={`https://img.vietqr.io/image/${PAYMENT_CONFIG.bankId}-${PAYMENT_CONFIG.accountNo}-compact.jpg?amount=${PAYMENT_CONFIG.amount}&addInfo=NangCapPro_${user?.email}`} 
                    alt="QR Code" 
                    className="w-full h-full object-contain" 
                />
              </div>

              <label className="block">
                <span className="text-xs font-black uppercase text-slate-400 block mb-2">Tải lên biên lai (Ảnh)</span>
                <div className="relative group cursor-pointer">
                  <div className={`border-2 border-dashed rounded-xl p-4 transition-all flex flex-col items-center justify-center gap-2 ${previewUrl ? 'border-brand-primary bg-brand-primary/5' : 'border-slate-200 dark:border-slate-800 hover:border-brand-primary'}`}>
                    {previewUrl ? (
                      <img src={previewUrl} className="h-20 w-auto rounded-lg object-cover" />
                    ) : (
                      <Upload className="text-slate-400 group-hover:text-brand-primary" />
                    )}
                    <span className="text-[10px] font-bold text-slate-500">{selectedFile ? selectedFile.name : 'Nhấn để chọn ảnh'}</span>
                  </div>
                  <input type="file" className="hidden" accept="image/*" onChange={handleFileChange} disabled={isLoading} />
                </div>
              </label>

              <button
                onClick={handleSubmit}
                disabled={isLoading || !selectedFile}
                className="w-full mt-6 bg-brand-primary text-white py-4 rounded-xl font-black uppercase tracking-widest text-xs shadow-xl shadow-brand-primary/20 hover:opacity-90 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
              >
                {isLoading ? <Loader2 className="animate-spin" /> : "Tôi đã thanh toán"}
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

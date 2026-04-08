import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { X, Mail, User, Lock, Bird, ArrowRight, Loader2 } from 'lucide-react';
import { useUser } from '../context/UserContext';
import { useToast } from './Toast';
import { useLanguage } from '../context/LanguageContext';
import { authService } from '../services/auth';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const { setAuthData } = useUser();
  const { showToast } = useToast();
  const { t } = useLanguage();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password || (!isLogin && !name)) {
      showToast(t('fillAllInfo'), 'error');
      return;
    }

    setIsLoading(true);

    try {
      if (isLogin) {
        // LUỒNG ĐĂNG NHẬP
        const tokens = await authService.login(email, password);
        localStorage.setItem('refresh_token', tokens.refresh_token);

        const userData = await authService.getMe(tokens.access_token);
        setAuthData(tokens.access_token, userData);

        showToast(t('loginSuccess'), 'success');
        onClose();
      } else {
        // LUỒNG ĐĂNG KÝ
        await authService.register(email, password, name);
        showToast(t('registerSuccess'), 'success');

        // Đăng ký xong, tự động đăng nhập
        const tokens = await authService.login(email, password);
        localStorage.setItem('refresh_token', tokens.refresh_token);
        const userData = await authService.getMe(tokens.access_token);
        setAuthData(tokens.access_token, userData);

        onClose();
      }
    } catch (error: any) {
      showToast(error.message || 'Có lỗi xảy ra, vui lòng thử lại', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
        />
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-md overflow-hidden rounded-[2rem] bg-white dark:bg-slate-900 shadow-[0_20px_60px_rgba(0,0,0,0.15)] dark:shadow-[0_20px_60px_rgba(0,0,0,0.5)] border border-slate-200/60 dark:border-slate-800/60"
        >
          <div className="p-8">
            <div className="mb-8 flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-primary text-white shadow-xl shadow-brand-primary/20">
                  <Bird size={20} strokeWidth={2.5} />
                </div>
                <span className="text-xl font-black tracking-tighter text-slate-950 dark:text-white font-display uppercase">ProductHunter</span>
              </div>
              <button onClick={onClose} className="rounded-full p-2 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
                <X size={20} />
              </button>
            </div>

            <div className="mb-8">
              <h2 className="text-3xl font-black text-slate-950 dark:text-white font-display leading-[1.1] tracking-tighter uppercase">
                {isLogin ? t('welcomeBack') : t('joinProductHunter')}
              </h2>
              <p className="mt-3 text-xs font-bold text-slate-500 dark:text-slate-400 leading-relaxed">
                {isLogin ? t('loginToSeeWishlist') : t('createAccountForAlerts')}
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {!isLogin && (
                <div className="relative group">
                  <User className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 group-focus-within:text-brand-primary transition-colors" />
                  <input
                    type="text"
                    placeholder={t('fullName')}
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    disabled={isLoading}
                    /* Dùng text-sm, font-medium, xóa uppercase và font-display */
                    className="w-full rounded-xl border-0 bg-slate-50 dark:bg-slate-950/50 py-4 pl-12 pr-5 text-sm font-medium text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-slate-800 transition-all focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-brand-primary outline-none disabled:opacity-50"
                  />
                </div>
              )}

              <div className="relative group">
                <Mail className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 group-focus-within:text-brand-primary transition-colors" />
                <input
                  type="email"
                  placeholder={t('yourEmail')}
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={isLoading}

                  className="w-full rounded-xl border-0 bg-slate-50 dark:bg-slate-950/50 py-4 pl-12 pr-5 text-sm font-medium text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-slate-800 transition-all focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-brand-primary outline-none disabled:opacity-50"
                />
              </div>

              <div className="relative group">
                <Lock className="absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400 group-focus-within:text-brand-primary transition-colors" />
                <input
                  type="password"
                  placeholder={t('password')}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isLoading}
                  className="w-full rounded-xl border-0 bg-slate-50 dark:bg-slate-950/50 py-4 pl-12 pr-5 text-sm font-medium text-slate-900 dark:text-white ring-1 ring-inset ring-slate-200 dark:ring-slate-800 transition-all focus:bg-white dark:focus:bg-slate-900 focus:ring-2 focus:ring-brand-primary outline-none disabled:opacity-50"
                />
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="group flex w-full items-center justify-center gap-2.5 rounded-xl bg-brand-primary py-4 text-[11px] font-black text-white shadow-xl shadow-brand-primary/20 transition-all hover:bg-brand-secondary active:scale-95 uppercase tracking-widest font-display disabled:opacity-70 disabled:pointer-events-none"
              >
                {isLoading ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <>
                    {isLogin ? t('login') : t('register')}
                    <ArrowRight size={16} className="transition-transform group-hover:translate-x-1" />
                  </>
                )}
              </button>
            </form>

            <div className="relative my-8">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200 dark:border-slate-800"></div>
              </div>
              <div className="relative flex justify-center text-[8px] uppercase tracking-[0.3em]">
                <span className="bg-white dark:bg-slate-900 px-3 font-black text-slate-400 font-display">{t('orContinueWith')}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => window.location.href = 'https://nanopi-r5c.tail47f64f.ts.net/api/v1/auth/google/login'}
                className="flex items-center justify-center gap-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 py-3 text-[10px] font-black text-slate-700 dark:text-slate-300 transition-all hover:bg-slate-50 dark:hover:bg-slate-800 active:scale-95 shadow-sm uppercase tracking-widest font-display"
              >
                <svg className="h-4 w-4" viewBox="0 0 24 24">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05" />
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
                </svg>
                Google
              </button>
              <button
                type="button"
                onClick={() => window.location.href = 'https://nanopi-r5c.tail47f64f.ts.net/api/v1/auth/github/login'}
                className="flex items-center justify-center gap-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 py-3 text-[10px] font-black text-slate-700 dark:text-slate-300 transition-all hover:bg-slate-50 dark:hover:bg-slate-800 active:scale-95 shadow-sm uppercase tracking-widest font-display"
              >
                <svg className="h-4 w-4 fill-current" viewBox="0 0 24 24">
                  <path d="M12 2C6.477 2 2 6.477 2 12c0 4.418 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.341-3.369-1.341-.454-1.152-1.11-1.459-1.11-1.459-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482C19.138 20.161 22 16.416 22 12c0-5.523-4.477-10-10-10z" />
                </svg>
                GitHub
              </button>
            </div>

            <div className="mt-8 text-center">
              <button
                onClick={() => setIsLogin(!isLogin)}
                className="text-[10px] font-black text-slate-500 hover:text-brand-primary transition-colors uppercase tracking-widest font-display"
              >
                {isLogin ? t('noAccountRegister') : t('haveAccountLogin')}
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
import React from 'react';
import { motion } from 'motion/react';
import { Bird, ArrowRight, Bell, ShieldAlert, Play, TrendingDown, History, Star, ShoppingCart, Store, ShoppingBag, Package, Users, Heart } from 'lucide-react';
import { AuthModal } from './AuthModal';
import { useLanguage } from '../context/LanguageContext';

export function LandingPage({ onStart }: { onStart: () => void }) {
  const [isAuthOpen, setIsAuthOpen] = React.useState(false);
  const { t } = useLanguage();

  return (
    <div className="min-h-screen bg-[#f4f5f7] dark:bg-[#050505] text-slate-900 dark:text-slate-100 selection:bg-brand-primary selection:text-white overflow-x-hidden font-sans transition-colors duration-300 relative">
      {/* Ambient Background Glows */}
      <div className="absolute top-0 left-1/4 w-[300px] md:w-[500px] h-[300px] md:h-[500px] rounded-full bg-brand-primary/20 dark:bg-brand-primary/15 blur-[80px] md:blur-[120px] pointer-events-none mix-blend-multiply dark:mix-blend-screen" />
      <div className="absolute bottom-0 right-1/4 w-[300px] md:w-[500px] h-[300px] md:h-[500px] rounded-full bg-blue-500/20 dark:bg-blue-500/15 blur-[80px] md:blur-[120px] pointer-events-none mix-blend-multiply dark:mix-blend-screen" />
      
      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-black/5 dark:border-white/5 bg-white/60 dark:bg-[#050505]/60 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-primary text-white shadow-lg shadow-brand-primary/20">
              <Bird size={18} strokeWidth={2.5} />
            </div>
            <span className="text-lg font-black tracking-tighter font-display uppercase">ProductHunter<span className="text-brand-primary">.</span></span>
          </div>
          
          <div className="hidden md:flex items-center gap-8">
            {[
              { id: 'features', label: t('features') },
              { id: 'platforms', label: t('platforms') },
              { id: 'community', label: t('community') }
            ].map((item) => (
              <a key={item.id} href={`#${item.id}`} className="text-xs font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400 hover:text-brand-primary dark:hover:text-brand-primary transition-colors font-display">
                {item.label}
              </a>
            ))}
          </div>

          <div className="flex items-center gap-3 sm:gap-4">
            <button 
              onClick={() => setIsAuthOpen(true)}
              className="hidden sm:block text-xs font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors font-display"
            >
              {t('login')}
            </button>
            <button 
              onClick={onStart}
              className="bg-slate-900 dark:bg-white text-white dark:text-slate-900 px-4 py-2 sm:px-6 sm:py-2.5 rounded-xl text-xs font-bold uppercase tracking-widest hover:bg-brand-primary dark:hover:bg-brand-primary dark:hover:text-white transition-all active:scale-95 shadow-xl shadow-black/10 dark:shadow-white/10 font-display"
            >
              {t('startNow')}
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="relative pt-32 pb-16 md:pt-40 md:pb-24 min-h-screen flex flex-col lg:grid lg:grid-cols-12 items-center justify-center max-w-[1440px] mx-auto px-6 gap-12 lg:gap-8 z-10">
        {/* Left Pane */}
        <div className="lg:col-span-5 xl:col-span-5 flex flex-col justify-center w-full text-center lg:text-left">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="flex flex-col items-center lg:items-start"
          >
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white dark:bg-white/5 border border-black/5 dark:border-white/10 shadow-sm mb-8">
              <span className="flex h-2 w-2 rounded-full bg-brand-primary animate-pulse" />
              <span className="text-[10px] font-bold uppercase tracking-widest text-brand-primary font-display">{t('huntDealsAI')}</span>
            </div>
            
            <h1 className="text-5xl sm:text-6xl lg:text-[4rem] xl:text-[5rem] font-black tracking-tighter mb-6 leading-tight font-display text-slate-900 dark:text-white uppercase">
              {t('smartShopping')}<br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-primary to-orange-400">
                {t('maxSavings')}
              </span>
            </h1>
            
            <p className="max-w-xl text-base sm:text-lg text-slate-600 dark:text-slate-400 font-medium mb-10 leading-relaxed mx-auto lg:mx-0">
              {t('heroDesc')}
            </p>

            <div className="flex flex-col sm:flex-row items-center gap-4 w-full sm:w-auto">
              <button 
                onClick={onStart}
                className="group w-full sm:w-auto flex items-center justify-center gap-3 bg-brand-primary px-8 py-4 rounded-2xl text-sm font-black text-white transition-all hover:bg-brand-primary/90 shadow-2xl shadow-brand-primary/25 uppercase tracking-widest font-display hover:-translate-y-1"
              >
                {t('startHunting')}
                <ArrowRight size={18} className="transition-transform group-hover:translate-x-1" />
              </button>
              <button 
                onClick={() => {
                  const featuresSection = document.getElementById('features');
                  if (featuresSection) {
                    featuresSection.scrollIntoView({ behavior: 'smooth' });
                  }
                }}
                className="group w-full sm:w-auto flex items-center justify-center gap-3 px-8 py-4 rounded-2xl text-sm font-black bg-white dark:bg-white/5 border border-black/5 dark:border-white/10 hover:bg-slate-50 dark:hover:bg-white/10 transition-all text-slate-700 dark:text-slate-200 shadow-sm uppercase tracking-widest font-display hover:-translate-y-1"
              >
                <Play size={18} fill="currentColor" className="transition-transform group-hover:scale-110 text-brand-primary" />
                {t('howItWorks')}
              </button>
            </div>
          </motion.div>
        </div>

        {/* Right Pane - Service Mockup */}
        <div className="lg:col-span-7 xl:col-span-7 w-full relative flex justify-center items-center mt-8 lg:mt-0">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 1, ease: [0.16, 1, 0.3, 1], delay: 0.2 }}
            className="relative z-10 w-full max-w-[540px] lg:max-w-[700px] xl:max-w-[800px]"
          >
            {/* Mockup Dashboard Window */}
            <div className="bg-white/90 dark:bg-[#0a0a0a]/90 backdrop-blur-2xl rounded-[2rem] shadow-[0_32px_64px_rgba(0,0,0,0.1)] dark:shadow-[0_32px_64px_rgba(0,0,0,0.5)] border border-white dark:border-white/10 overflow-hidden">
              {/* Window Header */}
              <div className="bg-slate-50/80 dark:bg-white/5 px-5 py-4 border-b border-black/5 dark:border-white/5 flex items-center justify-between">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-400/80" />
                  <div className="w-3 h-3 rounded-full bg-amber-400/80" />
                  <div className="w-3 h-3 rounded-full bg-emerald-400/80" />
                </div>
                <div className="bg-white dark:bg-black/50 px-4 py-1 rounded-full border border-black/5 dark:border-white/5 text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest font-display flex items-center gap-2">
                  <Bird size={10} className="text-brand-primary" />
                  ProductHunter.com
                </div>
                <div className="w-10" />
              </div>
              
              {/* Window Content */}
              <div className="p-6 sm:p-8">
                <div className="flex items-center justify-between mb-8">
                  <div className="space-y-1">
                    <div className="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest font-display">Live Tracking</div>
                    <div className="text-xl font-black text-slate-900 dark:text-white font-display uppercase tracking-tight">Market Pulse</div>
                  </div>
                  <div className="flex items-center gap-2 bg-emerald-50 dark:bg-emerald-500/10 px-3 py-1.5 rounded-full border border-emerald-100 dark:border-emerald-500/20">
                    <TrendingDown size={14} className="text-emerald-600 dark:text-emerald-400" />
                    <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">-24% Today</span>
                  </div>
                </div>

                {/* Conceptual Chart Visual */}
                <div className="h-48 flex items-end gap-2 mb-8 px-2">
                  {[30, 45, 35, 60, 55, 80, 75, 40, 30, 25, 20].map((h, i) => (
                    <motion.div 
                      key={i}
                      initial={{ height: 0 }}
                      animate={{ height: `${h}%` }}
                      transition={{ delay: 0.5 + i * 0.05, duration: 0.8 }}
                      className={`flex-1 rounded-t-lg transition-colors ${i === 10 ? 'bg-brand-primary shadow-[0_0_20px_rgba(242,125,38,0.4)]' : 'bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10'}`}
                    />
                  ))}
                </div>

                {/* Mockup List Items */}
                <div className="space-y-4">
                  {[1, 2].map((i) => (
                    <div key={i} className="flex items-center justify-between p-4 rounded-2xl bg-slate-50 dark:bg-white/5 border border-black/5 dark:border-white/5">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-xl bg-white dark:bg-black/50 border border-black/5 dark:border-white/5 shadow-sm flex items-center justify-center">
                          <div className="w-5 h-5 rounded-full bg-slate-200 dark:bg-slate-700" />
                        </div>
                        <div className="space-y-2">
                          <div className="h-2.5 w-24 bg-slate-200 dark:bg-slate-700 rounded-full animate-pulse" />
                          <div className="h-2 w-16 bg-slate-100 dark:bg-slate-800 rounded-full" />
                        </div>
                      </div>
                      <div className="h-4 w-12 bg-emerald-100 dark:bg-emerald-500/20 rounded-full" />
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Floating Notification Card */}
            <motion.div 
              initial={{ opacity: 0, y: 20, x: -20 }}
              animate={{ opacity: 1, y: 0, x: 0 }}
              transition={{ delay: 1.2, duration: 0.6 }}
              className="absolute -left-4 sm:-left-12 bottom-8 sm:bottom-12 bg-white/90 dark:bg-[#111]/90 backdrop-blur-xl p-4 sm:p-5 rounded-2xl shadow-[0_20px_40px_rgba(0,0,0,0.12)] dark:shadow-[0_20px_40px_rgba(0,0,0,0.6)] border border-white dark:border-white/10 flex items-center gap-4 max-w-[260px] sm:max-w-xs"
            >
              <div className="h-12 w-12 rounded-xl bg-brand-primary flex items-center justify-center text-white shadow-lg shadow-brand-primary/30 shrink-0">
                <Bell size={20} className="animate-[ring_4s_ease-in-out_infinite]" />
              </div>
              <div>
                <div className="text-[9px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest font-display mb-0.5">Price Alert</div>
                <div className="text-sm font-black text-slate-900 dark:text-white uppercase tracking-tight leading-tight">Target reached!</div>
              </div>
            </motion.div>
          </motion.div>
        </div>
      </main>

      {/* Features Section */}
      <section id="features" className="py-24 px-6 relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16 md:mb-24">
            <h2 className="text-3xl md:text-5xl font-black tracking-tighter mb-6 font-display uppercase text-slate-900 dark:text-white">
              {t('features')}
            </h2>
            <p className="text-base md:text-lg text-slate-500 dark:text-slate-400 max-w-2xl mx-auto font-medium">
              Discover how ProductHunter helps you save money and make smarter purchasing decisions with our advanced tracking tools.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 lg:gap-8">
            {/* Feature 1 */}
            <div className="bg-white/60 dark:bg-white/[0.02] backdrop-blur-xl p-8 lg:p-10 rounded-[2.5rem] border border-black/[0.03] dark:border-white/[0.05] shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.1)] hover:-translate-y-2 transition-transform duration-300 flex flex-col">
              <div className="h-14 w-14 rounded-2xl bg-white dark:bg-white/5 flex items-center justify-center text-brand-primary mb-8 shadow-sm border border-black/5 dark:border-white/5">
                <History size={24} />
              </div>
              <h3 className="text-xl lg:text-2xl font-black mb-4 font-display text-slate-900 dark:text-white tracking-tight uppercase">{t('priceHistory6Months')}</h3>
              <p className="text-slate-500 dark:text-slate-400 text-sm font-medium leading-relaxed mb-8 flex-1">{t('priceHistory6MonthsDesc')}</p>
              <div className="h-24 flex items-end gap-1.5 px-2">
                {[40, 70, 45, 90, 65, 80, 50, 85].map((h, i) => (
                  <div key={i} className="flex-1 bg-brand-primary/15 dark:bg-brand-primary/20 rounded-t-lg transition-all hover:bg-brand-primary/30" style={{ height: `${h}%` }} />
                ))}
              </div>
            </div>

            {/* Feature 2 */}
            <div className="bg-white/60 dark:bg-white/[0.02] backdrop-blur-xl p-8 lg:p-10 rounded-[2.5rem] border border-black/[0.03] dark:border-white/[0.05] shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.1)] hover:-translate-y-2 transition-transform duration-300 flex flex-col">
              <div className="h-14 w-14 rounded-2xl bg-white dark:bg-white/5 flex items-center justify-center text-brand-primary mb-8 shadow-sm border border-black/5 dark:border-white/5">
                <Bell size={24} />
              </div>
              <h3 className="text-xl lg:text-2xl font-black mb-4 font-display text-slate-900 dark:text-white tracking-tight uppercase">{t('priceAlerts')}</h3>
              <p className="text-slate-500 dark:text-slate-400 text-sm font-medium leading-relaxed mb-8 flex-1">{t('priceAlertsDesc')}</p>
              <div className="space-y-3">
                <div className="bg-white dark:bg-white/5 p-3.5 rounded-xl border border-black/5 dark:border-white/5 flex items-center gap-3 shadow-sm">
                  <div className="h-8 w-8 rounded-lg bg-brand-primary flex items-center justify-center text-white shadow-md shadow-brand-primary/20">
                    <Bell size={14} />
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-slate-900 dark:text-white">Price dropped to 1.2M₫</span>
                </div>
                <div className="bg-white/50 dark:bg-white/[0.02] p-3.5 rounded-xl border border-black/5 dark:border-white/5 flex items-center gap-3 opacity-60">
                  <div className="h-8 w-8 rounded-lg bg-slate-100 dark:bg-white/10 flex items-center justify-center text-slate-400 dark:text-slate-500">
                    <Bell size={14} />
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">New deal found</span>
                </div>
              </div>
            </div>

            {/* Feature 3 */}
            <div className="bg-white/60 dark:bg-white/[0.02] backdrop-blur-xl p-8 lg:p-10 rounded-[2.5rem] border border-black/[0.03] dark:border-white/[0.05] shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.1)] hover:-translate-y-2 transition-transform duration-300 flex flex-col md:col-span-2 lg:col-span-1">
              <div className="h-14 w-14 rounded-2xl bg-white dark:bg-white/5 flex items-center justify-center text-brand-primary mb-8 shadow-sm border border-black/5 dark:border-white/5">
                <ShieldAlert size={24} />
              </div>
              <h3 className="text-xl lg:text-2xl font-black mb-4 font-display text-slate-900 dark:text-white tracking-tight uppercase">{t('dealAnalysis')}</h3>
              <p className="text-slate-500 dark:text-slate-400 text-sm font-medium leading-relaxed mb-8 flex-1">{t('dealAnalysisDesc')}</p>
              <div className="mt-auto flex items-center gap-4 bg-emerald-50 dark:bg-emerald-500/10 p-5 rounded-2xl border border-emerald-100 dark:border-emerald-500/20">
                <div className="text-4xl font-black text-emerald-600 dark:text-emerald-400">9.5</div>
                <div className="space-y-1">
                  <div className="flex text-emerald-500">
                    {[1,2,3,4,5].map(star => <Star key={star} size={12} fill="currentColor" />)}
                  </div>
                  <div className="text-[10px] font-bold text-emerald-600/80 dark:text-emerald-400/80 uppercase tracking-widest font-display">{t('excellentDealScore')}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Platforms Section */}
      <section id="platforms" className="py-24 px-6 relative z-10 bg-white/30 dark:bg-white/[0.01] border-y border-black/5 dark:border-white/5">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-3xl md:text-5xl font-black tracking-tighter mb-6 font-display uppercase text-slate-900 dark:text-white">
            {t('platforms')}
          </h2>
          <p className="text-base md:text-lg text-slate-500 dark:text-slate-400 max-w-2xl mx-auto font-medium mb-16">
            We track prices across all major e-commerce platforms in Vietnam to ensure you never miss a deal.
          </p>
          
          <div className="flex flex-wrap justify-center gap-4 md:gap-8">
            {[
              { name: 'Shopee', color: 'text-[#ee4d2d]', bg: 'bg-[#ee4d2d]/10', icon: ShoppingBag },
              { name: 'Lazada', color: 'text-[#0f136d]', bg: 'bg-[#0f136d]/10', icon: ShoppingCart },
              { name: 'Tiki', color: 'text-[#1a94ff]', bg: 'bg-[#1a94ff]/10', icon: Package },
              { name: 'TikTok Shop', color: 'text-slate-900 dark:text-white', bg: 'bg-slate-100 dark:bg-white/10', icon: Store },
            ].map((platform) => (
              <div key={platform.name} className="flex items-center gap-3 px-6 py-4 rounded-2xl bg-white dark:bg-[#111] border border-black/5 dark:border-white/5 shadow-sm hover:-translate-y-1 transition-transform cursor-pointer">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${platform.bg} ${platform.color}`}>
                  <platform.icon size={20} />
                </div>
                <span className="text-lg font-black tracking-tight font-display">{platform.name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Community Section */}
      <section id="community" className="py-24 px-6 relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16 md:mb-24">
            <h2 className="text-3xl md:text-5xl font-black tracking-tighter mb-6 font-display uppercase text-slate-900 dark:text-white">
              {t('community')}
            </h2>
            <p className="text-base md:text-lg text-slate-500 dark:text-slate-400 max-w-2xl mx-auto font-medium">
              Join thousands of smart shoppers who are already saving money every day.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
            {[
              { name: 'Minh Tuấn', role: 'Smart Shopper', text: 'ProductHunter helped me save over 2M VND on my new laptop. The price drop alert was instant!', rating: 5 },
              { name: 'Hương Giang', role: 'Deal Hunter', text: 'I love the price history chart. It shows me exactly when a "sale" is actually just a fake discount.', rating: 5 },
              { name: 'Thành Nam', role: 'Tech Enthusiast', text: 'The best tool for tracking tech prices across Shopee and Tiki. Highly recommended!', rating: 5 },
            ].map((review, i) => (
              <div key={i} className="bg-white/60 dark:bg-white/[0.02] backdrop-blur-xl p-8 rounded-[2.5rem] border border-black/[0.03] dark:border-white/[0.05] shadow-[0_8px_30px_rgb(0,0,0,0.04)] dark:shadow-[0_8px_30px_rgb(0,0,0,0.1)] flex flex-col">
                <div className="flex text-amber-400 mb-6">
                  {[...Array(review.rating)].map((_, j) => <Star key={j} size={16} fill="currentColor" />)}
                </div>
                <p className="text-slate-700 dark:text-slate-300 font-medium leading-relaxed mb-8 flex-1">"{review.text}"</p>
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-brand-primary to-orange-400 flex items-center justify-center text-white font-bold text-lg">
                    {review.name.charAt(0)}
                  </div>
                  <div>
                    <div className="font-bold text-slate-900 dark:text-white">{review.name}</div>
                    <div className="text-xs text-slate-500 dark:text-slate-400">{review.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-8 text-center">
            {[
              { label: 'Active Users', value: '50K+', icon: Users },
              { label: 'Deals Found', value: '1M+', icon: ShoppingBag },
              { label: 'Money Saved', value: '10B+ ₫', icon: TrendingDown },
              { label: 'Reviews', value: '4.9/5', icon: Heart },
            ].map((stat, i) => (
              <div key={i} className="p-6 rounded-3xl bg-white/40 dark:bg-white/[0.01] border border-black/5 dark:border-white/5">
                <div className="w-10 h-10 mx-auto rounded-full bg-brand-primary/10 text-brand-primary flex items-center justify-center mb-4">
                  <stat.icon size={18} />
                </div>
                <div className="text-3xl font-black text-slate-900 dark:text-white font-display mb-1">{stat.value}</div>
                <div className="text-xs font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-32 px-6 relative z-10">
        <div className="max-w-5xl mx-auto bg-brand-primary rounded-[3rem] p-10 md:p-20 text-center relative overflow-hidden shadow-2xl shadow-brand-primary/20">
          <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(white 2px, transparent 2px)', backgroundSize: '30px 30px' }} />
          <div className="relative z-10">
            <h2 className="text-4xl md:text-6xl font-black tracking-tighter mb-6 font-display uppercase text-white">{t('readyToSave')}</h2>
            <p className="text-lg text-white/80 font-medium mb-10 max-w-xl mx-auto leading-relaxed">{t('joinUsersDesc')}</p>
            <button 
              onClick={onStart}
              className="bg-white text-brand-primary px-10 py-5 rounded-2xl text-sm font-black hover:bg-slate-50 transition-all hover:scale-105 active:scale-95 shadow-xl uppercase tracking-widest font-display inline-flex items-center gap-3"
            >
              {t('startFreeNow')}
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-black/5 dark:border-white/5 bg-white/50 dark:bg-[#050505]/50 backdrop-blur-lg relative z-10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-brand-primary text-white">
              <Bird size={18} strokeWidth={2.5} />
            </div>
            <span className="text-lg font-black tracking-tighter font-display uppercase text-slate-900 dark:text-white">ProductHunter<span className="text-brand-primary">.</span></span>
          </div>
          
          <div className="flex items-center gap-8">
            {['Twitter', 'Facebook', 'Instagram'].map((s) => (
              <a key={s} href="#" className="text-[10px] font-bold uppercase tracking-widest text-slate-400 dark:text-slate-500 hover:text-brand-primary dark:hover:text-brand-primary transition-colors font-display">{s}</a>
            ))}
          </div>

          <p className="text-[10px] font-bold text-slate-400 dark:text-slate-600 uppercase tracking-widest font-display">© 2024 ProductHunter</p>
        </div>
      </footer>

      <AuthModal isOpen={isAuthOpen} onClose={() => setIsAuthOpen(false)} />
    </div>
  );
}

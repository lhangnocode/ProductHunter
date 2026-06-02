import { useEffect, useState } from 'react';
import { ArrowLeft, Crown, Loader2, ShieldCheck, UserCog, CreditCard, Check, X, ExternalLink, Clock } from 'lucide-react';
import { adminService, AdminUser, AdminPaymentRequest } from '../services/admin';
import { useUser } from '../context/UserContext';
import { useToast } from './Toast';
import { CONFIG } from '../config';

const ADMIN_EMAILS = new Set(['lhang18022005@gmail.com', 'vinhlg@gmail.com']);

type AdminTab = 'users' | 'payments';

interface AdminPageProps {
  onBackHome: () => void;
}

export function AdminPage({ onBackHome }: AdminPageProps) {
  const { user } = useUser();
  const { showToast } = useToast();
  
  const [activeTab, setActiveTab] = useState<AdminTab>('users');
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [payments, setPayments] = useState<AdminPaymentRequest[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const isAdmin = !!user && ADMIN_EMAILS.has(user.email.toLowerCase());

  const token = localStorage.getItem('access_token') || '';

  const fetchData = async () => {
    if (!isAdmin || !token) return;
    setIsLoading(true);
    try {
      if (activeTab === 'users') {
        const data = await adminService.getUsers(token);
        setUsers(data);
      } else {
        const data = await adminService.getPaymentRequests(token);
        setPayments(data);
      }
    } catch (err: any) {
      showToast(err.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [activeTab, isAdmin]);

  const handleUpdatePlan = async (u: AdminUser, newPlan: number) => {
    setActionLoading(u.id);
    try {
      await adminService.updateUserPlan(token, u.id, newPlan);
      showToast("Cập nhật quyền hạn thành công", "success");
      fetchData();
    } catch (err: any) { showToast(err.message, "error"); }
    finally { setActionLoading(null); }
  };

  const handleProcessPayment = async (id: string, action: 'approve' | 'reject') => {
    setActionLoading(id);
    try {
      if (action === 'approve') await adminService.approvePayment(token, id);
      else await adminService.rejectPayment(token, id);
      
      showToast(action === 'approve' ? "Đã duyệt nâng cấp!" : "Đã từ chối yêu cầu", "success");
      fetchData();
    } catch (err: any) { showToast(err.message, "error"); }
    finally { setActionLoading(null); }
  };

  if (!isAdmin) return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950 p-6">
      <div className="max-w-md text-center p-8 bg-white dark:bg-slate-900 rounded-[2.5rem] shadow-xl">
        <ShieldCheck size={48} className="mx-auto text-rose-500 mb-4" />
        <h2 className="text-xl font-black uppercase font-display">Truy cập bị từ chối</h2>
        <button onClick={onBackHome} className="mt-6 bg-brand-primary text-white px-8 py-3 rounded-xl font-bold uppercase text-xs">Về trang chủ</button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-950 dark:text-white pb-20">
      <div className="max-w-6xl mx-auto px-6 pt-10">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-10">
          <div className="flex items-center gap-4">
            <button onClick={onBackHome} className="p-3 bg-white dark:bg-slate-900 rounded-2xl shadow-sm hover:scale-105 transition-transform">
              <ArrowLeft size={20} />
            </button>
            <div>
              <h1 className="text-3xl font-black font-display uppercase tracking-tighter">Hệ thống Quản trị</h1>
              <p className="text-sm text-slate-500 font-bold">Xin chào Admin, {user?.full_name}</p>
            </div>
          </div>

          <div className="flex p-1 bg-slate-200 dark:bg-slate-800 rounded-2xl">
            <button 
              onClick={() => setActiveTab('users')}
              className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-black uppercase transition-all ${activeTab === 'users' ? 'bg-white dark:bg-slate-900 shadow-md text-brand-primary' : 'text-slate-500'}`}
            >
              <UserCog size={16} /> Người dùng
            </button>
            <button 
              onClick={() => setActiveTab('payments')}
              className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-black uppercase transition-all ${activeTab === 'payments' ? 'bg-white dark:bg-slate-900 shadow-md text-brand-primary' : 'text-slate-500'}`}
            >
              <CreditCard size={16} /> Duyệt Pro
              {payments.filter(p => p.status === 0).length > 0 && (
                <span className="bg-rose-500 text-white w-5 h-5 rounded-full flex items-center justify-center text-[10px] animate-pulse">
                  {payments.filter(p => p.status === 0).length}
                </span>
              )}
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white dark:bg-slate-900 rounded-[2.5rem] shadow-sm border border-slate-200 dark:border-slate-800 overflow-hidden">
          {isLoading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-4 text-slate-400">
              <Loader2 className="animate-spin" size={32} />
              <p className="text-xs font-black uppercase tracking-widest">Đang tải dữ liệu...</p>
            </div>
          ) : activeTab === 'users' ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead className="bg-slate-50 dark:bg-slate-950/50 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-6 py-4 text-[10px] font-black uppercase text-slate-400">Người dùng</th>
                    <th className="px-6 py-4 text-[10px] font-black uppercase text-slate-400">Gói hiện tại</th>
                    <th className="px-6 py-4 text-[10px] font-black uppercase text-slate-400">Ngày tham gia</th>
                    <th className="px-6 py-4 text-[10px] font-black uppercase text-slate-400 text-right">Thao tác</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {users.map(u => (
                    <tr key={u.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-4">
                        <p className="font-bold text-sm">{u.full_name || 'Chưa đặt tên'}</p>
                        <p className="text-xs text-slate-500">{u.email}</p>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-black uppercase ${u.plan === 1 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-slate-100 text-slate-500 dark:bg-slate-800'}`}>
                          {u.plan === 1 ? <><Crown size={12}/> Pro</> : 'Free'}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-xs text-slate-500">
                        {new Date(u.created_at).toLocaleDateString('vi-VN')}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button 
                          onClick={() => handleUpdatePlan(u, u.plan === 1 ? 0 : 1)}
                          disabled={actionLoading === u.id}
                          className="text-[10px] font-black uppercase tracking-widest text-brand-primary hover:underline disabled:opacity-50"
                        >
                          {actionLoading === u.id ? '...' : u.plan === 1 ? 'Hạ cấp' : 'Nâng cấp'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
              {payments.length === 0 ? (
                <div className="col-span-full py-20 text-center text-slate-400 font-bold italic">Không có yêu cầu thanh toán nào</div>
              ) : (
                payments.map(p => (
                  <div key={p.id} className={`p-6 rounded-3xl border transition-all ${p.status === 0 ? 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 shadow-md ring-1 ring-brand-primary/10' : 'bg-slate-50 dark:bg-slate-950/40 border-transparent opacity-60'}`}>
                    <div className="flex justify-between items-start mb-6">
                      <div className="flex gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-brand-primary/10 text-brand-primary flex items-center justify-center">
                          <CreditCard size={24} />
                        </div>
                        <div>
                          <p className="font-black text-sm uppercase">{p.email}</p>
                          <div className="flex items-center gap-2 text-xs text-slate-500 font-bold mt-1">
                            <Clock size={12}/> {new Date(p.created_at).toLocaleString('vi-VN')}
                          </div>
                        </div>
                      </div>
                      <div className={`px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest ${p.status === 0 ? 'bg-blue-100 text-blue-600' : p.status === 1 ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'}`}>
                        {p.status === 0 ? 'Chờ duyệt' : p.status === 1 ? 'Đã duyệt' : 'Từ chối'}
                      </div>
                    </div>

                    <div className="mb-6">
                      <p className="text-[10px] font-black uppercase text-slate-400 mb-2">Số tiền chuyển khoản</p>
                      <p className="text-2xl font-black text-brand-primary font-mono">
                        {new Intl.NumberFormat('vi-VN').format(p.amount)}đ
                      </p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <a 
                        href={`${CONFIG.API_URL}${p.receipt_url}`} 
                        target="_blank" 
                        rel="noreferrer"
                        className="flex items-center justify-center gap-2 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 py-3 rounded-xl text-[10px] font-black uppercase hover:bg-slate-200 transition-colors"
                      >
                        <ExternalLink size={14} /> Xem biên lai
                      </a>
                      
                      {p.status === 0 && (
                        <div className="flex gap-2">
                          <button 
                            onClick={() => handleProcessPayment(p.id, 'reject')}
                            disabled={!!actionLoading}
                            className="flex-1 bg-rose-50 text-rose-500 py-3 rounded-xl hover:bg-rose-100 transition-colors"
                          >
                            <X size={18} className="mx-auto" />
                          </button>
                          <button 
                            onClick={() => handleProcessPayment(p.id, 'approve')}
                            disabled={!!actionLoading}
                            className="flex-[2] bg-emerald-500 text-white py-3 rounded-xl font-black text-[10px] uppercase shadow-lg shadow-emerald-500/20 hover:opacity-90 transition-all"
                          >
                            Duyệt ngay
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
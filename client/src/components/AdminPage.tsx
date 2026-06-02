import { useEffect, useState } from 'react';
import { ArrowLeft, Crown, Loader2, ShieldCheck, UserCog } from 'lucide-react';
import { adminService, AdminUser } from '../services/admin';
import { useUser } from '../context/UserContext';
import { useToast } from './Toast';

const ADMIN_EMAILS = new Set(['lhang18022005@gmail.com', 'vinhlg@gmail.com']);

interface AdminPageProps {
  onBackHome: () => void;
}

export function AdminPage({ onBackHome }: AdminPageProps) {
  const { user, isLoadingUser } = useUser();
  const { showToast } = useToast();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [updatingUserId, setUpdatingUserId] = useState<string | null>(null);

  const isAdmin = !!user && ADMIN_EMAILS.has(user.email.toLowerCase());

  useEffect(() => {
    const loadUsers = async () => {
      const token = localStorage.getItem('access_token');
      if (!token || !isAdmin) return;
      setIsLoading(true);
      try {
        const items = await adminService.getUsers(token);
        setUsers(items);
      } catch (error: any) {
        showToast(error.message || 'Không thể tải danh sách người dùng', 'error');
      } finally {
        setIsLoading(false);
      }
    };
    loadUsers();
  }, [isAdmin]);

  const updatePlan = async (targetUser: AdminUser, plan: 0 | 1) => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    setUpdatingUserId(targetUser.id);
    try {
      const updated = await adminService.updateUserPlan(token, targetUser.id, plan);
      setUsers((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      showToast(plan === 1 ? 'Đã nâng cấp người dùng lên Pro' : 'Đã chuyển người dùng về Free', 'success');
    } catch (error: any) {
      showToast(error.message || 'Không thể cập nhật gói người dùng', 'error');
    } finally {
      setUpdatingUserId(null);
    }
  };

  if (isLoadingUser) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 text-slate-500 dark:bg-slate-950">
        <Loader2 className="animate-spin" />
      </div>
    );
  }

  if (!isAdmin) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6 dark:bg-slate-950">
        <div className="max-w-md rounded-[2rem] bg-white p-8 text-center shadow-xl ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
          <ShieldCheck className="mx-auto mb-4 text-rose-500" size={40} />
          <h1 className="font-display text-2xl font-black uppercase text-slate-950 dark:text-white">Không có quyền truy cập</h1>
          <p className="mt-3 text-sm font-medium text-slate-500 dark:text-slate-400">Trang này chỉ dành cho admin.</p>
          <button
            onClick={onBackHome}
            className="mt-6 rounded-xl bg-brand-primary px-6 py-3 text-xs font-black uppercase tracking-widest text-white"
          >
            Về trang chính
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6 text-slate-950 dark:bg-slate-950 dark:text-white">
      <div className="mx-auto max-w-6xl">
        <button
          onClick={onBackHome}
          className="mb-6 flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-xs font-black uppercase tracking-widest text-slate-600 ring-1 ring-slate-200 dark:bg-slate-900 dark:text-slate-300 dark:ring-slate-800"
        >
          <ArrowLeft size={16} />
          Trang chính
        </button>

        <div className="mb-8 flex items-center gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-primary/10 text-brand-primary">
            <UserCog size={28} />
          </div>
          <div>
            <p className="text-[9px] font-black uppercase tracking-[0.3em] text-brand-primary">Admin</p>
            <h1 className="font-display text-3xl font-black uppercase tracking-tight">Quản lý người dùng</h1>
          </div>
        </div>

        <div className="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-slate-200 dark:bg-slate-900 dark:ring-slate-800">
          <div className="grid grid-cols-[1.6fr_1fr_0.6fr_0.9fr_0.9fr] gap-4 border-b border-slate-200 px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-400 dark:border-slate-800">
            <span>Email</span>
            <span>Tên</span>
            <span>Gói</span>
            <span>Ngày tạo</span>
            <span className="text-right">Thao tác</span>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-16 text-slate-400">
              <Loader2 className="animate-spin" />
            </div>
          ) : (
            users.map((item) => (
              <div
                key={item.id}
                className="grid grid-cols-[1.6fr_1fr_0.6fr_0.9fr_0.9fr] items-center gap-4 border-b border-slate-100 px-6 py-4 last:border-b-0 dark:border-slate-800"
              >
                <span className="truncate text-sm font-bold">{item.email}</span>
                <span className="truncate text-sm text-slate-500 dark:text-slate-400">{item.full_name || '-'}</span>
                <span>
                  <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[10px] font-black uppercase ${item.plan === 1 ? 'bg-brand-primary/10 text-brand-primary' : 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-300'}`}>
                    {item.plan === 1 && <Crown size={12} />}
                    {item.plan === 1 ? 'Pro' : 'Free'}
                  </span>
                </span>
                <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
                  {new Date(item.created_at).toLocaleDateString('vi-VN')}
                </span>
                <div className="text-right">
                  <button
                    onClick={() => updatePlan(item, item.plan === 1 ? 0 : 1)}
                    disabled={updatingUserId === item.id}
                    className={`rounded-xl px-4 py-2 text-[10px] font-black uppercase tracking-widest text-white transition-all disabled:cursor-wait disabled:opacity-60 ${item.plan === 1 ? 'bg-slate-700 hover:bg-slate-800' : 'bg-brand-primary hover:opacity-90'}`}
                  >
                    {updatingUserId === item.id ? 'Đang cập nhật' : item.plan === 1 ? 'Downgrade' : 'Upgrade'}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';
import {
  ArrowLeft,
  Bot,
  Boxes,
  Monitor,
  Clock,
  CreditCard,
  Crown,
  ExternalLink,
  LayoutDashboard,
  Loader2,
  MessageSquareText,
  PackageSearch,
  Settings,
  ShieldCheck,
  Store,
  Tags,
  UserCog,
  X,
} from 'lucide-react';
import type { LucideIcon } from 'lucide-react';
import { adminService, AdminUser, AdminPaymentRequest } from '../services/admin';
import { useUser } from '../context/UserContext';
import { useToast } from './Toast';
import { CONFIG } from '../config';
import { AdminAgentPanel } from './AdminAgentPanel';

const ADMIN_EMAILS = new Set([
  'lhang18022005@gmail.com',
  'vinhlg@gmail.com',
  'testbank@gmail.com',
  'letridangg2005@gmail.com',
  '23020715@vnu.edu.vn',
  'nguyenhaibatrung05@gmail.com',
]);

type AdminTab =
  | 'overview'
  | 'users'
  | 'payments'
  | 'shops'
  | 'products'
  | 'offers'
  | 'agent'
  | 'conversations'
  | 'settings';

interface AdminNavItem {
  id: AdminTab;
  label: string;
  description: string;
  icon: LucideIcon;
  status?: 'ready' | 'planned';
}

const ADMIN_NAV_ITEMS: AdminNavItem[] = [
  {
    id: 'overview',
    label: 'Overview',
    description: 'Platform snapshot',
    icon: LayoutDashboard,
    status: 'planned',
  },
  {
    id: 'users',
    label: 'Users',
    description: 'Plans and access',
    icon: UserCog,
    status: 'ready',
  },
  {
    id: 'payments',
    label: 'Payments',
    description: 'Pro approvals',
    icon: CreditCard,
    status: 'ready',
  },
  {
    id: 'shops',
    label: 'Shops',
    description: 'Managed sellers',
    icon: Store,
    status: 'planned',
  },
  {
    id: 'products',
    label: 'Products',
    description: 'Catalog records',
    icon: PackageSearch,
    status: 'planned',
  },
  {
    id: 'offers',
    label: 'Shop Offers',
    description: 'Prices and stock',
    icon: Tags,
    status: 'planned',
  },
  {
    id: 'agent',
    label: 'Agent',
    description: 'Telesales assistant',
    icon: Bot,
    status: 'ready',
  },
  {
    id: 'conversations',
    label: 'Conversations',
    description: 'Agent sessions',
    icon: MessageSquareText,
    status: 'planned',
  },
  {
    id: 'settings',
    label: 'Settings',
    description: 'Platform config',
    icon: Settings,
    status: 'planned',
  },
];

interface AdminPageProps {
  onBackHome: () => void;
}

export function AdminPage({ onBackHome }: AdminPageProps) {
  const { user } = useUser();
  const { showToast } = useToast();
  
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [payments, setPayments] = useState<AdminPaymentRequest[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const isAdmin = !!user && ADMIN_EMAILS.has(user.email.toLowerCase());

  const token = localStorage.getItem('access_token') || '';

  const pendingPaymentsCount = payments.filter(p => p.status === 0).length;
  const activeNavItem = ADMIN_NAV_ITEMS.find(item => item.id === activeTab) || ADMIN_NAV_ITEMS[0];
  const ActiveIcon = activeNavItem.icon;
  const adminFontStyle = {
    fontFamily: 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  };

  const fetchData = async () => {
    if (!isAdmin || !token) return;
    if (activeTab !== 'users' && activeTab !== 'payments') return;

    setIsLoading(true);
    try {
      if (activeTab === 'users') {
        const data = await adminService.getUsers(token);
        setUsers(data);
      } else if (activeTab === 'payments') {
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

  const renderOverview = () => (
    <div className="p-6">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-white dark:bg-slate-950 p-5 rounded-lg shadow-sm">
          <p className="text-xs font-medium text-slate-400 mb-2">Ready modules</p>
          <p className="text-3xl font-semibold">3</p>
          <p className="text-xs text-slate-500 mt-1">Users, Payments, and Agent are wired to APIs.</p>
        </div>
        <div className="bg-white dark:bg-slate-950 p-5 rounded-lg shadow-sm">
          <p className="text-xs font-medium text-slate-400 mb-2">Planned modules</p>
          <p className="text-3xl font-semibold">6</p>
          <p className="text-xs text-slate-500 mt-1">Shop, catalog, agent, and conversation surfaces.</p>
        </div>
        <div className="bg-white dark:bg-slate-950 p-5 rounded-lg shadow-sm">
          <p className="text-xs font-medium text-slate-400 mb-2">Pending payments</p>
          <p className="text-3xl font-semibold">{pendingPaymentsCount}</p>
          <p className="text-xs text-slate-500 mt-1">Visit Payments to refresh approval requests.</p>
        </div>
      </div>

      <div className="rounded-lg p-6 bg-white dark:bg-slate-950 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-slate-100 dark:bg-slate-900 text-slate-700 dark:text-slate-200 flex items-center justify-center">
            <Bot size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-sm" style={adminFontStyle}>Agentic platform direction</h3>
            <p className="text-xs text-slate-500">Phase 1 exposes the dashboard shell before backend and agent services are added.</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-slate-600 dark:text-slate-300">
          <div className="flex items-center gap-2"><Boxes size={16} className="text-slate-500" /> Shop and product management</div>
          <div className="flex items-center gap-2"><PackageSearch size={16} className="text-slate-500" /> Product database search tools</div>
          <div className="flex items-center gap-2"><Bot size={16} className="text-slate-500" /> LangChain agent service layer</div>
          <div className="flex items-center gap-2"><MessageSquareText size={16} className="text-slate-500" /> Agent conversations</div>
        </div>
      </div>
    </div>
  );

  const renderPlaceholder = (
    title: string,
    description: string,
    items: string[],
    Icon: LucideIcon,
  ) => (
    <div className="p-8 min-h-[420px] flex items-center justify-center">
      <div className="max-w-2xl w-full rounded-lg p-8 bg-white dark:bg-slate-950 shadow-sm">
        <div className="w-14 h-14 rounded-lg bg-slate-100 dark:bg-slate-900 text-slate-700 dark:text-slate-200 flex items-center justify-center mb-5">
          <Icon size={28} />
        </div>
        <p className="text-xs font-medium text-slate-400 mb-2">Phase 1 UI shell</p>
        <h3 className="text-2xl font-semibold mb-3" style={adminFontStyle}>{title}</h3>
        <p className="text-sm text-slate-500 mb-6">{description}</p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {items.map(item => (
            <div key={item} className="flex items-center gap-2 text-sm font-bold text-slate-600 dark:text-slate-300">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
              {item}
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderUsers = () => (
    <div className="overflow-x-auto">
      <table className="w-full text-left border-collapse">
        <thead className="bg-slate-50 dark:bg-slate-950/50 border-b border-slate-200 dark:border-slate-800">
          <tr>
            <th className="px-6 py-4 text-xs font-medium text-slate-400">Người dùng</th>
            <th className="px-6 py-4 text-xs font-medium text-slate-400">Gói hiện tại</th>
            <th className="px-6 py-4 text-xs font-medium text-slate-400">Ngày tham gia</th>
            <th className="px-6 py-4 text-xs font-medium text-slate-400 text-right">Thao tác</th>
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
                <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${u.plan === 1 ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400' : 'bg-slate-100 text-slate-500 dark:bg-slate-800'}`}>
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
                  className="text-xs font-medium text-slate-700 dark:text-slate-200 hover:underline disabled:opacity-50"
                >
                  {actionLoading === u.id ? '...' : u.plan === 1 ? 'Hạ cấp' : 'Nâng cấp'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const renderPayments = () => (
    <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
      {payments.length === 0 ? (
        <div className="col-span-full py-20 text-center text-slate-400 font-bold italic">Không có yêu cầu thanh toán nào</div>
      ) : (
        payments.map(p => (
          <div key={p.id} className={`p-6 rounded-lg transition-colors ${p.status === 0 ? 'bg-white dark:bg-slate-950 shadow-sm' : 'bg-slate-50 dark:bg-slate-950/40 opacity-70'}`}>
            <div className="flex justify-between items-start mb-6">
              <div className="flex gap-4">
                <div className="w-12 h-12 rounded-lg bg-slate-100 dark:bg-slate-900 text-slate-700 dark:text-slate-200 flex items-center justify-center">
                  <CreditCard size={24} />
                </div>
                <div>
                  <p className="font-semibold text-sm">{p.email}</p>
                  <div className="flex items-center gap-2 text-xs text-slate-500 font-bold mt-1">
                    <Clock size={12}/> {new Date(p.created_at).toLocaleString('vi-VN')}
                  </div>
                </div>
              </div>
              <div className={`px-3 py-1 rounded-lg text-xs font-medium ${p.status === 0 ? 'bg-blue-100 text-blue-600' : p.status === 1 ? 'bg-emerald-100 text-emerald-600' : 'bg-rose-100 text-rose-600'}`}>
                {p.status === 0 ? 'Chờ duyệt' : p.status === 1 ? 'Đã duyệt' : 'Từ chối'}
              </div>
            </div>

            <div className="mb-6">
              <p className="text-xs font-medium text-slate-400 mb-2">Số tiền chuyển khoản</p>
              <p className="text-2xl font-medium text-slate-950 dark:text-white tabular-nums">
                {new Intl.NumberFormat('vi-VN').format(p.amount)}đ
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <a 
                href={`${CONFIG.API_URL}${p.receipt_url}`} 
                target="_blank" 
                rel="noreferrer"
                className="flex items-center justify-center gap-2 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 py-3 rounded-xl text-xs font-medium hover:bg-slate-200 transition-colors"
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
                    className="flex-[2] bg-slate-950 dark:bg-white text-white dark:text-slate-950 py-3 rounded-lg font-medium text-xs hover:opacity-90 transition-opacity"
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
  );

  const renderContent = () => {
    if (isLoading && (activeTab === 'users' || activeTab === 'payments')) {
      return (
        <div className="py-20 flex flex-col items-center justify-center gap-4 text-slate-400">
          <Loader2 className="animate-spin" size={32} />
          <p className="text-xs font-medium">Đang tải dữ liệu...</p>
        </div>
      );
    }

    if (activeTab === 'overview') return renderOverview();
    if (activeTab === 'users') return renderUsers();
    if (activeTab === 'payments') return renderPayments();
    if (activeTab === 'shops') {
      return renderPlaceholder('Shops', 'Manage seller/shop profiles before the product and offer management APIs are added.', [
        'Shop profile and status',
        'Owner and contact details',
        'Business policies',
        'Catalog ownership',
      ], Store);
    }
    if (activeTab === 'products') {
      return renderPlaceholder('Products', 'Manage normalized product identities, specs, aliases, and search visibility.', [
        'Product catalog records',
        'Brand, model, category',
        'Specs and images',
        'Typesense reindex action',
      ], PackageSearch);
    }
    if (activeTab === 'offers') {
      return renderPlaceholder('Shop Offers', 'Manage shop-specific prices, stock state, URLs, promotions, and crawl/manual freshness.', [
        'Current and original price',
        'Stock and promotion labels',
        'Shop URL and affiliate URL',
        'Last updated timestamp',
      ], Tags);
    }
    if (activeTab === 'agent') {
      return <AdminAgentPanel />;
    }
    if (activeTab === 'conversations') {
      return renderPlaceholder('Conversations', 'Review future telesales conversations, tool calls, recommended products, and operator feedback.', [
        'Conversation history',
        'Recommended products',
        'Source inspection',
        'Operator feedback',
      ], MessageSquareText);
    }
    return renderPlaceholder('Settings', 'Control platform settings for API providers, agent streaming, crawler status, and migration workflow.', [
      'Agent provider config',
      'Agent transport settings',
      'Crawler and pipeline status',
      'Alembic migration workflow',
    ], Settings);
  };

  if (!isAdmin) return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950 p-6">
      <div className="max-w-md text-center p-8 bg-white dark:bg-slate-900 rounded-lg shadow-sm">
        <ShieldCheck size={48} className="mx-auto text-rose-500 mb-4" />
        <h2 className="text-xl font-semibold" style={adminFontStyle}>Truy cập bị từ chối</h2>
        <button onClick={onBackHome} className="mt-6 bg-slate-950 dark:bg-white text-white dark:text-slate-950 px-8 py-3 rounded-lg font-medium text-xs">Về trang chủ</button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-100 dark:bg-slate-950 text-slate-950 dark:text-white" style={adminFontStyle}>
      <div className="lg:hidden min-h-screen flex items-center justify-center p-6">
        <div className="w-full max-w-md bg-white dark:bg-slate-900 rounded-lg p-8 text-center shadow-sm">
          <div className="mx-auto mb-5 w-14 h-14 rounded-lg bg-slate-100 dark:bg-slate-950 flex items-center justify-center text-slate-700 dark:text-slate-200">
            <Monitor size={28} />
          </div>
          <p className="text-xs font-medium text-slate-400 mb-2">Desktop required</p>
          <h2 className="text-2xl font-semibold mb-3" style={adminFontStyle}>Use the dashboard on desktop</h2>
          <p className="text-sm text-slate-500 mb-6">This admin console is designed for wide-screen product, shop, and agent operations. Please open it on a desktop screen.</p>
          <button onClick={onBackHome} className="w-full bg-slate-950 dark:bg-white text-white dark:text-slate-950 px-5 py-3 rounded-lg font-medium text-xs">
            Back Home
          </button>
        </div>
      </div>

      <div className="hidden lg:block w-full px-6 py-6">
        <div className="grid grid-cols-[280px_minmax(0,1fr)] gap-6">
          <aside className="bg-white dark:bg-slate-900 rounded-lg shadow-sm overflow-hidden sticky top-6 self-start">
            <div className="p-5">
              <button onClick={onBackHome} className="mb-5 flex items-center gap-2 text-xs font-medium text-slate-500 hover:text-slate-950 dark:hover:text-white transition-colors">
                <ArrowLeft size={16} />
                Home
              </button>
              <p className="text-xs font-medium text-slate-400 mb-2">ProductHunter</p>
              <h1 className="text-xl font-semibold" style={adminFontStyle}>Admin Console</h1>
              <p className="text-xs text-slate-500 font-bold mt-2">Xin chào Admin, {user?.full_name}</p>
            </div>

            <nav className="p-3 space-y-1">
              {ADMIN_NAV_ITEMS.map(item => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left transition-colors ${
                      isActive
                        ? 'bg-slate-950 text-white dark:bg-white dark:text-slate-950'
                        : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
                    }`}
                  >
                    <span className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                      isActive ? 'bg-white/10 text-current dark:bg-slate-950/10' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'
                    }`}>
                      <Icon size={18} />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-2">
                        <span className="block text-xs font-medium truncate">{item.label}</span>
                        {item.id === 'payments' && pendingPaymentsCount > 0 && (
                          <span className="bg-rose-500 text-white w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-semibold">
                            {pendingPaymentsCount}
                          </span>
                        )}
                      </span>
                      <span className={`block text-[11px] truncate ${isActive ? 'text-white/70' : 'text-slate-400'}`}>
                        {item.description}
                      </span>
                    </span>
                  </button>
                );
              })}
            </nav>
          </aside>

          <main className="min-w-0">
            <div className="mb-6 flex flex-col md:flex-row md:items-end justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-white dark:bg-slate-900 flex items-center justify-center text-slate-700 dark:text-slate-200 shadow-sm">
                  <ActiveIcon size={24} />
                </div>
                <div>
                  <p className="text-xs font-medium text-slate-400">Admin dashboard</p>
                  <h2 className="text-3xl font-semibold" style={adminFontStyle}>{activeNavItem.label}</h2>
                </div>
              </div>
            </div>

            <div className={activeTab === 'agent' ? 'overflow-hidden' : 'bg-slate-50 dark:bg-slate-900 rounded-lg shadow-sm overflow-hidden'}>
              {renderContent()}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

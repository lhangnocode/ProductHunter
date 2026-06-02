import React from 'react';

interface Props {
  currentPage: number;
  totalPages: number;
  onPageChange: (p: number) => void;
}

export function Pagination({ currentPage, totalPages, onPageChange }: Props) {
  const showPageButtons = totalPages > 1;

  // 1. Chặn lỗi currentPage nằm ngoài khoảng an toàn (vd: lọc dữ liệu làm giảm số trang)
  const safeCurrentPage = Math.max(1, Math.min(currentPage, totalPages));

  const buildPages = () => {
    const pages: (number | -1)[] = [];
    const start = Math.max(1, safeCurrentPage - 2);
    const end = Math.min(totalPages, safeCurrentPage + 2);

    if (start > 1) pages.push(1);
    if (start > 2) pages.push(-1); // Dấu ba chấm
    for (let i = start; i <= end; i++) pages.push(i);
    if (end < totalPages - 1) pages.push(-1); // Dấu ba chấm
    if (end < totalPages) pages.push(totalPages);

    return pages;
  };

  if (!showPageButtons) return null;

  return (
    // 2. Đổi <div> thành <nav> và thêm aria-label
    <nav aria-label="Pagination" className="mt-8 flex items-center justify-center gap-3">
      <button
        onClick={() => onPageChange(Math.max(1, safeCurrentPage - 1))}
        disabled={safeCurrentPage <= 1}
        className={`rounded-md px-3 py-2 text-sm font-black uppercase tracking-wider ${
          safeCurrentPage <= 1
            ? 'opacity-40 cursor-not-allowed'
            : 'bg-white dark:bg-slate-900 ring-1 ring-inset ring-slate-200 dark:ring-slate-800 shadow-sm'
        }`}
        title={safeCurrentPage <= 1 ? 'Đã ở trang đầu' : 'Trang trước'}
      >
        Previous
      </button>

      <div className="flex items-center gap-2">
        {buildPages().map((p, idx) =>
          p === -1 ? (
            <span key={`e-${idx}`} className="px-2 text-sm text-slate-400">
              …
            </span>
          ) : (
            <button
              key={`p-${p}`}
              onClick={() => {
                // console.debug('[Pagination] page click ->', p, 'currentPage=', safeCurrentPage, 'totalPages=', totalPages);
                onPageChange(p);
              }}
              aria-current={p === safeCurrentPage ? 'page' : undefined} // 3. Hỗ trợ Accessibility
              className={`min-w-[38px] rounded-md px-3 py-2 text-sm font-black ${
                p === safeCurrentPage
                  ? 'bg-brand-primary text-white'
                  : 'bg-white dark:bg-slate-900 ring-1 ring-inset ring-slate-200 dark:ring-slate-800'
              }`}
            >
              {p}
            </button>
          ),
        )}
      </div>

      <button
        onClick={() => onPageChange(Math.min(totalPages, safeCurrentPage + 1))}
        disabled={safeCurrentPage >= totalPages}
        className={`rounded-md px-3 py-2 text-sm font-black uppercase tracking-wider ${
          safeCurrentPage >= totalPages
            ? 'opacity-40 cursor-not-allowed'
            : 'bg-white dark:bg-slate-900 ring-1 ring-inset ring-slate-200 dark:ring-slate-800 shadow-sm'
        }`}
        title={safeCurrentPage >= totalPages ? 'Không còn trang tiếp theo' : 'Trang tiếp theo'}
      >
        Next
      </button>
    </nav>
  );
}
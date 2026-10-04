import React, { useEffect, useState } from 'react';
import { CheckCircle2, XCircle, Clock, FileText, User, ShieldAlert, Check } from 'lucide-react';
import { approvalsApi } from '../services/api';
import type { Approval, PaginatedResponse } from '../types';
import ApprovalDialog from '../components/ApprovalDialog';

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'PENDING':
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-900/30 px-2.5 py-0.5 text-xs font-medium text-amber-400 border border-amber-500/30"><Clock size={12} /> Pending</span>;
    case 'APPROVED':
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-900/30 px-2.5 py-0.5 text-xs font-medium text-emerald-400 border border-emerald-500/30"><Check size={12} /> Approved</span>;
    case 'REJECTED':
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-red-900/30 px-2.5 py-0.5 text-xs font-medium text-red-400 border border-red-500/30"><XCircle size={12} /> Rejected</span>;
    case 'EXPIRED':
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-800 px-2.5 py-0.5 text-xs font-medium text-gray-400 border border-gray-600"><Clock size={12} /> Expired</span>;
    default:
      return <span className="inline-flex items-center gap-1.5 rounded-full bg-gray-700 px-2.5 py-0.5 text-xs font-medium text-gray-300">{status}</span>;
  }
};

const Approvals: React.FC = () => {
  const [data, setData] = useState<PaginatedResponse<Approval> | null>(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [activeTab, setActiveTab] = useState<'PENDING' | 'ALL'>('PENDING');
  const size = 20;

  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedApproval, setSelectedApproval] = useState<Approval | null>(null);
  const [dialogType, setDialogType] = useState<'approve' | 'reject'>('approve');

  const fetchApprovals = async () => {
    setLoading(true);
    try {
      const params: Record<string, unknown> = { page, size };
      if (activeTab === 'PENDING') {
        params.status = 'PENDING';
      }
      const response = await approvalsApi.list(params);
      setData(response);
    } catch (err) {
      console.error('Failed to fetch approvals', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApprovals();
  }, [page, activeTab]);

  const openDialog = (approval: Approval, type: 'approve' | 'reject') => {
    setSelectedApproval(approval);
    setDialogType(type);
    setDialogOpen(true);
  };

  const handleAction = async (id: number, action: 'approve' | 'reject', comment?: string) => {
    try {
      if (action === 'approve') {
        await approvalsApi.approve(id, comment);
      } else {
        await approvalsApi.reject(id, comment);
      }
      setDialogOpen(false);
      fetchApprovals(); // Refresh list
    } catch (err) {
      console.error(`Failed to ${action} request`, err);
      alert(`Failed to ${action} request. Check console for details.`);
    }
  };

  return (
    <div className="space-y-6 flex flex-col h-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2">
          <CheckCircle2 className="text-cyan-400" />
          Approval Workflow
        </h2>
        
        <div className="flex items-center gap-4">
          <div className="flex rounded-lg bg-gray-800 p-1 border border-gray-700">
            <button
              onClick={() => { setActiveTab('PENDING'); setPage(1); }}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                activeTab === 'PENDING'
                  ? 'bg-gray-700 text-white shadow-sm'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              Pending
            </button>
            <button
              onClick={() => { setActiveTab('ALL'); setPage(1); }}
              className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
                activeTab === 'ALL'
                  ? 'bg-gray-700 text-white shadow-sm'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              All Requests
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden rounded-xl border border-gray-700 bg-gray-800 shadow-xl flex flex-col">
        {loading && !data ? (
          <div className="flex-1 flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent"></div>
          </div>
        ) : data?.items.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center py-12 text-center">
            <div className="rounded-full bg-gray-700/50 p-4 mb-4 text-gray-500">
              <CheckCircle2 size={32} />
            </div>
            <p className="text-lg font-medium text-gray-300">No {activeTab.toLowerCase()} approvals.</p>
            <p className="text-sm text-gray-500 mt-1">You're all caught up!</p>
          </div>
        ) : (
          <div className="overflow-y-auto flex-1 p-4 space-y-4">
            {data?.items.map((approval) => (
              <div key={approval.id} className="rounded-lg border border-gray-700 bg-gray-900/50 p-5 transition-colors hover:border-gray-600">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-sm text-cyan-400">#{approval.request_id.split('-')[0]}</span>
                      {getStatusBadge(approval.status)}
                      <span className="text-xs text-gray-500">
                        Requested {new Date(approval.created_at).toLocaleString()}
                      </span>
                    </div>
                    
                    <div className="flex flex-col gap-2 text-sm text-gray-300">
                      <div className="flex items-start gap-2">
                        <FileText size={16} className="text-gray-500 shrink-0 mt-0.5" />
                        <span><span className="text-gray-500">Reason:</span> {approval.reason || 'No reason provided'}</span>
                      </div>
                      {approval.requester && (
                        <div className="flex items-center gap-2">
                          <User size={16} className="text-gray-500 shrink-0" />
                          <span><span className="text-gray-500">Requester:</span> {approval.requester.username}</span>
                        </div>
                      )}
                      {approval.requested_action && (
                        <div className="flex items-center gap-2">
                          <ShieldAlert size={16} className="text-gray-500 shrink-0" />
                          <span><span className="text-gray-500">Action:</span> {approval.requested_action}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {approval.status === 'PENDING' && (
                    <div className="flex sm:flex-col gap-2 shrink-0">
                      <button
                        onClick={() => openDialog(approval, 'approve')}
                        className="flex items-center justify-center gap-1.5 rounded-md bg-emerald-600/20 px-4 py-2 text-sm font-medium text-emerald-400 border border-emerald-500/30 hover:bg-emerald-600/30 transition-colors"
                      >
                        <Check size={16} />
                        Approve
                      </button>
                      <button
                        onClick={() => openDialog(approval, 'reject')}
                        className="flex items-center justify-center gap-1.5 rounded-md bg-red-600/20 px-4 py-2 text-sm font-medium text-red-400 border border-red-500/30 hover:bg-red-600/30 transition-colors"
                      >
                        <XCircle size={16} />
                        Reject
                      </button>
                    </div>
                  )}
                  
                  {approval.status !== 'PENDING' && approval.reviewer && (
                    <div className="text-right text-sm text-gray-500">
                      <p>Reviewed by {approval.reviewer.username}</p>
                      {approval.reviewed_at && (
                        <p>{new Date(approval.reviewed_at).toLocaleString()}</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <ApprovalDialog
        isOpen={dialogOpen}
        approval={selectedApproval}
        type={dialogType}
        onClose={() => setDialogOpen(false)}
        onConfirm={handleAction}
      />
    </div>
  );
};

export default Approvals;

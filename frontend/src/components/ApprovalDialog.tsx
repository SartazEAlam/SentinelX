import React from 'react';
import { AlertTriangle, ShieldAlert } from 'lucide-react';
import type { Approval } from '../types';

interface ApprovalDialogProps {
  approval: Approval | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (id: number, action: 'approve' | 'reject', comment?: string) => void;
  type: 'approve' | 'reject';
}

export default function ApprovalDialog({
  approval,
  isOpen,
  onClose,
  onConfirm,
  type,
}: ApprovalDialogProps) {
  const [comment, setComment] = React.useState('');

  if (!isOpen || !approval) return null;

  const isApprove = type === 'approve';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-lg border border-gray-700 bg-gray-800 p-6 shadow-xl">
        <div className="mb-6 flex items-center gap-3">
          <div
            className={`flex h-10 w-10 items-center justify-center rounded-full ${
              isApprove ? 'bg-emerald-500/10 text-emerald-500' : 'bg-red-500/10 text-red-500'
            }`}
          >
            {isApprove ? <ShieldAlert size={20} /> : <AlertTriangle size={20} />}
          </div>
          <h2 className="text-xl font-semibold text-white">
            {isApprove ? 'Approve Operation' : 'Deny Operation'}
          </h2>
        </div>

        <div className="mb-6 space-y-4 text-sm text-gray-300">
          <div className="rounded border border-gray-700 bg-gray-900/50 p-4 space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-400">Request ID</span>
              <span className="font-mono text-cyan-400">{approval.request_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Operation</span>
              <span className="font-mono">{approval.requested_action || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Requester</span>
              <span className="font-mono">{approval.requester?.username || 'System'}</span>
            </div>
            <div className="flex flex-col gap-1 mt-2 border-t border-gray-700 pt-2">
              <span className="text-gray-400">Reason</span>
              <span className="text-gray-300 italic">{approval.reason || 'No reason provided'}</span>
            </div>
          </div>

          <div>
            <label htmlFor="comment" className="mb-2 block text-sm font-medium text-gray-400">
              Justification (Optional)
            </label>
            <textarea
              id="comment"
              rows={3}
              className="w-full rounded border border-gray-700 bg-gray-900 px-3 py-2 text-white placeholder-gray-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="Enter reason for this decision..."
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
          </div>
        </div>

        <div className="flex justify-end gap-3">
          <button
            onClick={onClose}
            className="rounded px-4 py-2 text-sm font-medium text-gray-300 hover:bg-gray-700"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              onConfirm(approval.id, type, comment);
              setComment('');
            }}
            className={`rounded px-4 py-2 text-sm font-medium text-white ${
              isApprove
                ? 'bg-emerald-600 hover:bg-emerald-500'
                : 'bg-red-600 hover:bg-red-500'
            }`}
          >
            {isApprove ? 'Approve' : 'Deny'}
          </button>
        </div>
      </div>
    </div>
  );
}

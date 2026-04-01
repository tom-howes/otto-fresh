"use client";

import { useState, useEffect } from "react";
import Avatar from "@/components/ui/Avatar";
import { workspaceApi, BackendComment } from "@/utils/api";

interface CommentsSectionProps {
  workspaceId: string | null;
  issueId: string;
}

export default function CommentsSection({ workspaceId, issueId }: CommentsSectionProps) {
  const [comments, setComments] = useState<BackendComment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [commentPosting, setCommentPosting] = useState(false);
  const [editingCommentId, setEditingCommentId] = useState<string | null>(null);
  const [editCommentText, setEditCommentText] = useState("");
  const [commentEditing, setCommentEditing] = useState(false);

  useEffect(() => {
    if (!workspaceId) return;
    workspaceApi.getComments(workspaceId, issueId)
      .then(res => setComments(res.comments ?? []))
      .catch(() => {});
  }, [workspaceId, issueId]);

  const handleAddComment = async () => {
    if (!newComment.trim() || !workspaceId || commentPosting) return;
    const tempId = `temp-${Date.now()}`;
    const optimistic = { id: tempId, content: newComment.trim(), author_id: "?", created_at: new Date().toISOString(), updated_at: new Date().toISOString() };
    setComments(prev => [...prev, optimistic]);
    setNewComment("");
    setCommentPosting(true);
    try {
      const comment = await workspaceApi.addComment(workspaceId, issueId, optimistic.content);
      setComments(prev => prev.map(c => c.id === tempId ? comment : c));
    } catch {
      setComments(prev => prev.filter(c => c.id !== tempId));
    } finally {
      setCommentPosting(false);
    }
  };

  const handleEditComment = async (commentId: string) => {
    if (!workspaceId || !editCommentText.trim() || commentEditing) return;
    setCommentEditing(true);
    try {
      const updated = await workspaceApi.updateComment(workspaceId, issueId, commentId, editCommentText.trim());
      setComments(prev => prev.map(c => c.id === commentId ? updated : c));
      setEditingCommentId(null);
    } catch { /* keep editing open */ } finally {
      setCommentEditing(false);
    }
  };

  return (
    <div className="border-t border-gray-100 dark:border-gray-800 pt-4">
      <h3 className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-3">
        Comments {comments.length > 0 && <span className="normal-case font-normal">({comments.length})</span>}
      </h3>

      {comments.length === 0 && (
        <p className="text-xs text-gray-300 dark:text-gray-600 mb-3">No comments yet.</p>
      )}

      <div className="space-y-3 mb-4">
        {comments.map(c => (
          <div key={c.id} className="flex items-start gap-3 group">
            <Avatar letter={String(c.author_id ?? "?").slice(0, 1).toUpperCase()} />
            <div className="flex-1">
              {editingCommentId === c.id ? (
                <div className="space-y-1.5">
                  <textarea
                    value={editCommentText}
                    onChange={e => setEditCommentText(e.target.value)}
                    rows={2}
                    autoFocus
                    className="w-full rounded-lg border border-violet-300 dark:border-violet-500/50 bg-white dark:bg-gray-900 px-3 py-1.5 text-xs text-gray-600 dark:text-gray-300 outline-none resize-none"
                  />
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => void handleEditComment(c.id)}
                      disabled={commentEditing || !editCommentText.trim()}
                      className="rounded-lg bg-violet-500 hover:bg-violet-600 disabled:opacity-50 px-2.5 py-1 text-xs font-medium text-white transition-colors"
                    >
                      {commentEditing ? "…" : "Save"}
                    </button>
                    <button
                      onClick={() => setEditingCommentId(null)}
                      className="rounded-lg border border-gray-200 dark:border-gray-700 px-2.5 py-1 text-xs text-gray-400 dark:text-gray-500 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">{c.content}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <p className="text-xs text-gray-300 dark:text-gray-600">
                      {new Date(c.created_at).toLocaleString()}
                    </p>
                    <button
                      onClick={() => { setEditingCommentId(c.id); setEditCommentText(c.content); }}
                      className="opacity-0 group-hover:opacity-100 text-xs text-gray-300 dark:text-gray-600 hover:text-violet-500 dark:hover:text-violet-400 transition-all"
                    >
                      Edit
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        ))}
      </div>

      {workspaceId && (
        <div className="flex gap-2">
          <input
            value={newComment}
            onChange={e => setNewComment(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleAddComment()}
            placeholder="Add a comment…"
            className="flex-1 rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 px-3 py-1.5 text-xs text-gray-600 dark:text-gray-300 outline-none placeholder-gray-300 dark:placeholder-gray-600"
          />
          <button
            onClick={handleAddComment}
            disabled={commentPosting || !newComment.trim()}
            className="rounded-lg bg-violet-500 hover:bg-violet-600 disabled:opacity-50 px-3 py-1.5 text-xs font-medium text-white transition-colors"
          >
            {commentPosting ? "…" : "Post"}
          </button>
        </div>
      )}
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { useProject } from '../hooks/useProject';
import { apiClient } from '../api/client';

interface ProjectDetails {
    project_id: string;
    name: string;
    description?: string;
    owner_id: string;
    role: 'owner' | 'admin' | 'member' | 'viewer';
    member_count: number;
    created_at: string;
    updated_at?: string;
}

interface TeamMember {
    user_id: string;
    email: string;
    role: 'owner' | 'admin' | 'member' | 'viewer';
    joined_at: string;
}

export default function ProjectsPage() {
    const { currentProject, projects, refreshProjects } = useProject();
    const [selectedProject, setSelectedProject] = useState<ProjectDetails | null>(null);
    const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
    const [loading, setLoading] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showDeleteModal, setShowDeleteModal] = useState(false);
    const [showInviteModal, setShowInviteModal] = useState(false);

    const [editForm, setEditForm] = useState({ name: '', description: '' });
    const [inviteEmail, setInviteEmail] = useState('');
    const [inviteRole, setInviteRole] = useState<'admin' | 'member' | 'viewer'>('member');

    useEffect(() => {
        if (currentProject) {
            loadProjectDetails(currentProject.project_id);
        }
    }, [currentProject]);

    const loadProjectDetails = async (projectId: string) => {
        try {
            setLoading(true);
            const response = await apiClient.get(`/projects/${projectId}`);
            setSelectedProject(response.data);

            // Load team members (if endpoint exists)
            try {
                const membersResponse = await apiClient.get(`/projects/${projectId}/members`);
                setTeamMembers(membersResponse.data);
            } catch (error) {
                // Members endpoint might not exist yet
                console.log('Team members endpoint not available');
                setTeamMembers([]);
            }
        } catch (error) {
            console.error('Failed to load project details:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleEditProject = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedProject) return;

        try {
            await apiClient.put(`/projects/${selectedProject.project_id}`, editForm);
            await refreshProjects();
            await loadProjectDetails(selectedProject.project_id);
            setShowEditModal(false);
        } catch (error) {
            console.error('Failed to update project:', error);
            alert('Failed to update project');
        }
    };

    const handleDeleteProject = async () => {
        if (!selectedProject) return;

        try {
            await apiClient.delete(`/projects/${selectedProject.project_id}`);
            await refreshProjects();
            setShowDeleteModal(false);
        } catch (error) {
            console.error('Failed to delete project:', error);
            alert('Failed to delete project');
        }
    };

    const handleInviteMember = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedProject) return;

        try {
            await apiClient.post(`/projects/${selectedProject.project_id}/members`, {
                email: inviteEmail,
                role: inviteRole,
            });
            await loadProjectDetails(selectedProject.project_id);
            setShowInviteModal(false);
            setInviteEmail('');
            setInviteRole('member');
        } catch (error) {
            console.error('Failed to invite member:', error);
            alert('Failed to invite team member');
        }
    };

    const handleRemoveMember = async (userId: string) => {
        if (!selectedProject) return;
        if (!confirm('Are you sure you want to remove this team member?')) return;

        try {
            await apiClient.delete(`/projects/${selectedProject.project_id}/members/${userId}`);
            await loadProjectDetails(selectedProject.project_id);
        } catch (error) {
            console.error('Failed to remove member:', error);
            alert('Failed to remove team member');
        }
    };

    const handleUpdateMemberRole = async (userId: string, newRole: string) => {
        if (!selectedProject) return;

        try {
            await apiClient.patch(`/projects/${selectedProject.project_id}/members/${userId}`, {
                role: newRole,
            });
            await loadProjectDetails(selectedProject.project_id);
        } catch (error) {
            console.error('Failed to update member role:', error);
            alert('Failed to update member role');
        }
    };

    const openEditModal = () => {
        if (selectedProject) {
            setEditForm({
                name: selectedProject.name,
                description: selectedProject.description || '',
            });
            setShowEditModal(true);
        }
    };

    const canManageProject = selectedProject?.role === 'owner' || selectedProject?.role === 'admin';
    const isOwner = selectedProject?.role === 'owner';

    if (loading && !selectedProject) {
        return (
            <div className="p-6">
                <div className="text-center py-12">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading project...</p>
                </div>
            </div>
        );
    }

    if (!selectedProject) {
        return (
            <div className="p-6">
                <div className="text-center py-12">
                    <p className="text-gray-600">No project selected</p>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">{selectedProject.name}</h1>
                    <p className="mt-1 text-gray-600">{selectedProject.description || 'No description'}</p>
                </div>
                {canManageProject && (
                    <div className="flex gap-2">
                        <button
                            onClick={openEditModal}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                        >
                            Edit Project
                        </button>
                        {isOwner && (
                            <button
                                onClick={() => setShowDeleteModal(true)}
                                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                            >
                                Delete Project
                            </button>
                        )}
                    </div>
                )}
            </div>

            {/* Project Info Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white p-6 rounded-lg shadow">
                    <div className="text-sm text-gray-600">Your Role</div>
                    <div className="mt-2 text-2xl font-bold text-gray-900 capitalize">{selectedProject.role}</div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                    <div className="text-sm text-gray-600">Team Members</div>
                    <div className="mt-2 text-2xl font-bold text-gray-900">{selectedProject.member_count}</div>
                </div>
                <div className="bg-white p-6 rounded-lg shadow">
                    <div className="text-sm text-gray-600">Created</div>
                    <div className="mt-2 text-2xl font-bold text-gray-900">
                        {new Date(selectedProject.created_at).toLocaleDateString()}
                    </div>
                </div>
            </div>

            {/* Team Members Section */}
            <div className="bg-white rounded-lg shadow">
                <div className="p-6 border-b border-gray-200 flex items-center justify-between">
                    <h2 className="text-xl font-bold text-gray-900">Team Members</h2>
                    {canManageProject && (
                        <button
                            onClick={() => setShowInviteModal(true)}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                            </svg>
                            Invite Member
                        </button>
                    )}
                </div>
                <div className="p-6">
                    {teamMembers.length === 0 ? (
                        <p className="text-center text-gray-600 py-8">No team members yet</p>
                    ) : (
                        <div className="space-y-4">
                            {teamMembers.map((member) => (
                                <div
                                    key={member.user_id}
                                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                                >
                                    <div className="flex items-center gap-4">
                                        <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-bold">
                                            {member.email.charAt(0).toUpperCase()}
                                        </div>
                                        <div>
                                            <div className="font-medium text-gray-900">{member.email}</div>
                                            <div className="text-sm text-gray-600">
                                                Joined {new Date(member.joined_at).toLocaleDateString()}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        {canManageProject && member.role !== 'owner' ? (
                                            <select
                                                value={member.role}
                                                onChange={(e) => handleUpdateMemberRole(member.user_id, e.target.value)}
                                                className="px-3 py-1 border border-gray-300 rounded text-sm"
                                            >
                                                <option value="admin">Admin</option>
                                                <option value="member">Member</option>
                                                <option value="viewer">Viewer</option>
                                            </select>
                                        ) : (
                                            <span className="px-3 py-1 bg-gray-200 rounded text-sm font-medium capitalize">
                                                {member.role}
                                            </span>
                                        )}
                                        {canManageProject && member.role !== 'owner' && (
                                            <button
                                                onClick={() => handleRemoveMember(member.user_id)}
                                                className="text-red-600 hover:text-red-700"
                                            >
                                                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path
                                                        strokeLinecap="round"
                                                        strokeLinejoin="round"
                                                        strokeWidth={2}
                                                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                                    />
                                                </svg>
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Edit Project Modal */}
            {showEditModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Edit Project</h2>
                        <form onSubmit={handleEditProject} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Project Name
                                </label>
                                <input
                                    type="text"
                                    value={editForm.name}
                                    onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Description
                                </label>
                                <textarea
                                    value={editForm.description}
                                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                    rows={3}
                                />
                            </div>
                            <div className="flex justify-end gap-2">
                                <button
                                    type="button"
                                    onClick={() => setShowEditModal(false)}
                                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                                >
                                    Save Changes
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Delete Project Modal */}
            {showDeleteModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold text-red-600 mb-4">Delete Project</h2>
                        <p className="text-gray-700 mb-6">
                            Are you sure you want to delete <strong>{selectedProject.name}</strong>? This action cannot be undone.
                            All data, API keys, and team members will be removed.
                        </p>
                        <div className="flex justify-end gap-2">
                            <button
                                onClick={() => setShowDeleteModal(false)}
                                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleDeleteProject}
                                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
                            >
                                Delete Project
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Invite Member Modal */}
            {showInviteModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md">
                        <h2 className="text-xl font-bold text-gray-900 mb-4">Invite Team Member</h2>
                        <form onSubmit={handleInviteMember} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Email Address
                                </label>
                                <input
                                    type="email"
                                    value={inviteEmail}
                                    onChange={(e) => setInviteEmail(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                    placeholder="colleague@example.com"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Role
                                </label>
                                <select
                                    value={inviteRole}
                                    onChange={(e) => setInviteRole(e.target.value as any)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                                >
                                    <option value="admin">Admin - Full access except project deletion</option>
                                    <option value="member">Member - Can view and create resources</option>
                                    <option value="viewer">Viewer - Read-only access</option>
                                </select>
                            </div>
                            <div className="flex justify-end gap-2">
                                <button
                                    type="button"
                                    onClick={() => setShowInviteModal(false)}
                                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                                >
                                    Send Invite
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}

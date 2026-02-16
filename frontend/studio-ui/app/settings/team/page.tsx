'use client';

import * as React from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { SectionPanel } from '@/components/agent-builder/section-panel';
import { Input, Select } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

// Types
interface TeamMember {
  user_id: string;
  email: string;
  name: string | null;
  role: 'owner' | 'admin' | 'member' | 'viewer';
  joined_at: string;
}

interface Team {
  id: string;
  name: string;
  slug: string;
  owner_id: string | null;
  created_at: string;
  members_count: number;
  members?: TeamMember[];
}

const ROLE_OPTIONS = [
  { value: 'viewer', label: 'Viewer - Read only access' },
  { value: 'member', label: 'Member - Create and edit agents' },
  { value: 'admin', label: 'Admin - Manage team members' },
  { value: 'owner', label: 'Owner - Full control' },
];

export default function TeamSettingsPage() {
  const [teams, setTeams] = React.useState<Team[]>([]);
  const [selectedTeam, setSelectedTeam] = React.useState<Team | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [showNewTeam, setShowNewTeam] = React.useState(false);
  const [showInvite, setShowInvite] = React.useState(false);

  const [newTeamName, setNewTeamName] = React.useState('');
  const [newTeamSlug, setNewTeamSlug] = React.useState('');
  const [inviteEmail, setInviteEmail] = React.useState('');
  const [inviteRole, setInviteRole] = React.useState('member');

  // Fetch teams on mount
  React.useEffect(() => {
    fetchTeams();
  }, []);

  const fetchTeams = async () => {
    try {
      const res = await fetch('http://localhost:8001/api/teams', {
        headers: {
          'X-User-Id': '00000000-0000-0000-0000-000000000000',
          'X-User-Email': 'dev@laias.local',
          'X-User-Name': 'Dev User',
        },
      });
      if (res.ok) {
        const data = await res.json();
        setTeams(data);
        if (data.length > 0) {
          setSelectedTeam(data[0]);
          fetchTeamDetails(data[0].id);
        }
      }
    } catch (e) {
      console.error('Failed to fetch teams', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchTeamDetails = async (teamId: string) => {
    try {
      const res = await fetch(`http://localhost:8001/api/teams/${teamId}`, {
        headers: {
          'X-User-Id': '00000000-0000-0000-0000-000000000000',
        },
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedTeam(data);
        // Update in list too
        setTeams(prev => prev.map(t => t.id === data.id ? data : t));
      }
    } catch (e) {
      console.error('Failed to fetch team details', e);
    }
  };

  const createTeam = async () => {
    if (!newTeamName.trim()) return;

    try {
      const res = await fetch('http://localhost:8001/api/teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': '00000000-0000-0000-0000-000000000000',
        },
        body: JSON.stringify({
          name: newTeamName,
          slug: newTeamSlug || undefined,
        }),
      });

      if (res.ok) {
        const newTeam = await res.json();
        setTeams(prev => [...prev, newTeam]);
        setSelectedTeam(newTeam);
        setNewTeamName('');
        setNewTeamSlug('');
        setShowNewTeam(false);
        fetchTeamDetails(newTeam.id);
      }
    } catch (e) {
      console.error('Failed to create team', e);
    }
  };

  const addMember = async () => {
    if (!selectedTeam || !inviteEmail.trim()) return;

    // For dev mode: generate a valid UUID v4 from email
    // In production, this would be a real user lookup/invitation flow
    const emailBytes = new TextEncoder().encode(inviteEmail.trim().toLowerCase());
    let hash = 0;
    for (let i = 0; i < emailBytes.length; i++) {
      hash = ((hash << 5) - hash) + emailBytes[i];
      hash = hash & hash;
    }
    // Generate a valid UUID v4 format
    const hex = Math.abs(hash).toString(16).padStart(12, '0');
    const mockUserId = `00000000-0000-4000-8000-${hex.padEnd(12, '0')}`;

    try {
      const res = await fetch(`http://localhost:8001/api/teams/${selectedTeam.id}/members`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': '00000000-0000-0000-0000-000000000000',
        },
        body: JSON.stringify({
          user_id: mockUserId,
          role: inviteRole,
        }),
      });

      if (res.ok) {
        setInviteEmail('');
        setInviteRole('member');
        setShowInvite(false);
        fetchTeamDetails(selectedTeam.id);
      } else {
        const error = await res.json();
        alert(error.detail || 'Failed to add member');
      }
    } catch (e) {
      console.error('Failed to add member', e);
    }
  };

  const updateMemberRole = async (userId: string, newRole: string) => {
    if (!selectedTeam) return;

    try {
      await fetch(`http://localhost:8001/api/teams/${selectedTeam.id}/members/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': '00000000-0000-0000-0000-000000000000',
        },
        body: JSON.stringify({ role: newRole }),
      });
      fetchTeamDetails(selectedTeam.id);
    } catch (e) {
      console.error('Failed to update role', e);
    }
  };

  const removeMember = async (userId: string) => {
    if (!selectedTeam) return;

    try {
      await fetch(`http://localhost:8001/api/teams/${selectedTeam.id}/members/${userId}`, {
        method: 'DELETE',
        headers: {
          'X-User-Id': '00000000-0000-0000-0000-000000000000',
        },
      });
      fetchTeamDetails(selectedTeam.id);
    } catch (e) {
      console.error('Failed to remove member', e);
    }
  };

  return (
    <AppShell title="Team Settings">
      <div className="max-w-4xl space-y-6">
        {/* Team Selector */}
        <SectionPanel title="Your Teams" accentColor="purple">
          <div className="space-y-4">
            {loading ? (
              <p className="text-sm text-gray-500">Loading teams...</p>
            ) : teams.length === 0 ? (
              <p className="text-sm text-gray-500">No teams yet. Create your first team!</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {teams.map((team) => (
                  <Card
                    key={team.id}
                    variant="interactive"
                    selected={selectedTeam?.id === team.id}
                    className="cursor-pointer"
                    onClick={() => {
                      setSelectedTeam(team);
                      fetchTeamDetails(team.id);
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-white">{team.name}</h3>
                        <p className="text-xs text-gray-500">{team.members_count} members</p>
                      </div>
                      <div className={`w-2 h-2 rounded-full ${
                        selectedTeam?.id === team.id ? 'bg-purple-500' : 'bg-gray-600'
                      }`} />
                    </div>
                  </Card>
                ))}
              </div>
            )}

            <Button
              variant="outline"
              className="w-full border-dashed"
              onClick={() => setShowNewTeam(!showNewTeam)}
            >
              {showNewTeam ? 'Cancel' : '+ Create New Team'}
            </Button>

            {showNewTeam && (
              <div className="space-y-3 p-4 bg-gray-900/50 rounded-lg border border-gray-800">
                <Input
                  label="Team Name"
                  placeholder="My Awesome Team"
                  value={newTeamName}
                  onChange={(e) => {
                    setNewTeamName(e.target.value);
                    if (!newTeamSlug) {
                      setNewTeamSlug(e.target.value.toLowerCase().replace(/\s+/g, '-'));
                    }
                  }}
                />
                <Input
                  label="Team Slug (optional)"
                  placeholder="my-awesome-team"
                  value={newTeamSlug}
                  onChange={(e) => setNewTeamSlug(e.target.value)}
                />
                <Button
                  variant="primary"
                  className="w-full"
                  onClick={createTeam}
                  disabled={!newTeamName.trim()}
                >
                  Create Team
                </Button>
              </div>
            )}
          </div>
        </SectionPanel>

        {/* Team Members */}
        {selectedTeam && (
          <SectionPanel
            title={`${selectedTeam.name} - Members`}
            accentColor="cyan"
          >
            <div className="space-y-4">
              {/* Invite Member */}
              <div className="flex gap-3">
                <Input
                  placeholder="Enter email to invite..."
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="flex-1"
                />
                <Select
                  value={inviteRole}
                  options={ROLE_OPTIONS}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-48"
                />
                <Button
                  variant="primary"
                  onClick={addMember}
                  disabled={!inviteEmail.trim()}
                >
                  Invite
                </Button>
              </div>

              {/* Members List */}
              <div className="space-y-2">
                {!selectedTeam.members || selectedTeam.members.length === 0 ? (
                  <p className="text-sm text-gray-500 py-4 text-center">No members yet. Invite someone to get started!</p>
                ) : (
                  selectedTeam.members.map((member) => (
                    <div
                      key={member.user_id}
                      className="flex items-center justify-between p-3 bg-gray-900/50 rounded-lg border border-gray-800"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-cyan-500 flex items-center justify-center text-sm font-medium">
                          {member.name?.[0]?.toUpperCase() || member.email[0].toUpperCase()}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-white">{member.name || 'Unknown'}</p>
                          <p className="text-xs text-gray-500">{member.email}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <select
                          value={member.role}
                          onChange={(e) => updateMemberRole(member.user_id, e.target.value)}
                          className="px-2 py-1 text-sm bg-gray-800 border border-gray-700 rounded text-white"
                          disabled={member.role === 'owner'}
                        >
                          <option value="owner">Owner</option>
                          <option value="admin">Admin</option>
                          <option value="member">Member</option>
                          <option value="viewer">Viewer</option>
                        </select>

                        {member.role !== 'owner' && (
                          <button
                            onClick={() => removeMember(member.user_id)}
                            className="p-1 text-gray-500 hover:text-red-400 transition-colors"
                          >
                            ×
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </SectionPanel>
        )}

        {/* Team Info */}
        {selectedTeam && (
          <SectionPanel title="Team Information" accentColor="pink">
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Team ID</span>
                <span className="text-white font-mono text-xs">{selectedTeam.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Slug</span>
                <span className="text-white">{selectedTeam.slug}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Created</span>
                <span className="text-white">
                  {new Date(selectedTeam.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          </SectionPanel>
        )}
      </div>
    </AppShell>
  );
}

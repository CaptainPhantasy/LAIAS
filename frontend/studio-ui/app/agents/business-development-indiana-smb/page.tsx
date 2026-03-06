'use client';

import { useState, useEffect } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input, Textarea, Select } from '@/components/ui/input';
import { studioApi } from '@/lib/api';
import { cn, formatDate, formatRelativeTime } from '@/lib/utils';
import { 
  Users, 
  Target, 
  TrendingUp, 
  Calendar, 
  DollarSign, 
  BarChart3,
  Play,
  Pause,
  RotateCcw,
  Activity,
  MapPin,
  Building,
  Mail,
  Phone,
  Send,
  CheckCircle,
  Clock,
  XCircle,
  Settings,
  Code,
  Globe,
  Bot
} from 'lucide-react';
import type { AgentSummary } from '@/types';

export default function IndianaSMBBusinessDevAgent() {
  const [agentStatus, setAgentStatus] = useState<'idle' | 'running' | 'paused' | 'completed' | 'error'>('idle');
  const [progress, setProgress] = useState(0);
  const [currentPhase, setCurrentPhase] = useState('Not started');
  const [metrics, setMetrics] = useState({
    leadsGenerated: 0,
    qualifiedLeads: 0,
    meetingsScheduled: 0,
    dealsClosed: 0,
    revenueProjected: 0
  });
  const [campaignSettings, setCampaignSettings] = useState({
    targetIndustries: ['Healthcare', 'Manufacturing', 'Legal'],
    targetGeography: 'Indiana (Brown County, Columbus, Bloomington, Indianapolis, 100-mile radius)',
    campaignDuration: 30, // days
    dailyOutreachLimit: 10,
    budgetPerLead: 50,
    serviceFocus: ['software', 'website'],
    outreachChannels: ['email', 'linkedin']
  });
  const [activeTab, setActiveTab] = useState('dashboard');

  // Mock function to simulate agent execution
  const handleStartCampaign = async () => {
    setAgentStatus('running');
    setProgress(0);
    setCurrentPhase('Initializing...');
    
    // Simulate the agent running through different phases
    const phases = [
      { name: 'Market Research', duration: 2000, description: 'Identifying high-value prospects in Indiana SMB market' },
      { name: 'Content Creation', duration: 3000, description: 'Creating personalized outreach content for each prospect' },
      { name: 'Outreach Execution', duration: 5000, description: 'Executing multi-channel outreach campaign' },
      { name: 'Lead Qualification', duration: 4000, description: 'Qualifying leads using BANT framework' },
      { name: 'Proposal Development', duration: 3000, description: 'Creating compelling proposals for qualified leads' },
      { name: 'Deal Closure', duration: 2000, description: 'Closing deals with qualified prospects' },
      { name: 'Metrics Analysis', duration: 1000, description: 'Analyzing campaign performance and optimizing strategies' }
    ];
    
    let cumulativeProgress = 0;
    for (const [index, phase] of phases.entries()) {
      setCurrentPhase(phase.name);
      
      // Simulate progress within this phase
      const phaseStartProgress = cumulativeProgress;
      const phaseEndProgress = ((index + 1) / phases.length) * 100;
      
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, phase.duration / 10));
        const currentPhaseProgress = phaseStartProgress + (phaseEndProgress - phaseStartProgress) * (i / 100);
        setProgress(Math.min(99, Math.round(currentPhaseProgress)));
        
        // Update metrics progressively
        setMetrics(prev => ({
          ...prev,
          leadsGenerated: Math.min(78, Math.floor(currentPhaseProgress * 0.8)),
          qualifiedLeads: Math.min(23, Math.floor(currentPhaseProgress * 0.25)),
          meetingsScheduled: Math.min(8, Math.floor(currentPhaseProgress * 0.1)),
          dealsClosed: Math.min(3, Math.floor(currentPhaseProgress * 0.05)),
          revenueProjected: Math.min(125000, Math.floor(currentPhaseProgress * 1200))
        }));
      }
      
      cumulativeProgress = phaseEndProgress;
    }
    
    setProgress(100);
    setCurrentPhase('Campaign Completed');
    setAgentStatus('completed');
    
    // Final metrics update
    setMetrics({
      leadsGenerated: 78,
      qualifiedLeads: 23,
      meetingsScheduled: 8,
      dealsClosed: 3,
      revenueProjected: 125000
    });
  };

  const handlePauseCampaign = () => {
    setAgentStatus('paused');
  };

  const handleResetCampaign = () => {
    setAgentStatus('idle');
    setProgress(0);
    setCurrentPhase('Not started');
    setMetrics({
      leadsGenerated: 0,
      qualifiedLeads: 0,
      meetingsScheduled: 0,
      dealsClosed: 0,
      revenueProjected: 0
    });
  };

  // Tab navigation
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
    { id: 'configuration', label: 'Configuration', icon: Settings },
    { id: 'results', label: 'Results', icon: TrendingUp },
    { id: 'analytics', label: 'Analytics', icon: Activity }
  ];

  return (
    <AppShell 
      title="Indiana SMB Business Development Agent" 
      actions={
        <div className="flex gap-3">
          {agentStatus === 'idle' || agentStatus === 'completed' || agentStatus === 'error' ? (
            <Button 
              variant="primary" 
              size="sm" 
              iconLeft={<Play className="w-4 h-4" />}
              onClick={handleStartCampaign}
            >
              Start Campaign
            </Button>
          ) : agentStatus === 'running' ? (
            <Button 
              variant="outline" 
              size="sm" 
              iconLeft={<Pause className="w-4 h-4" />}
              onClick={handlePauseCampaign}
            >
              Pause Campaign
            </Button>
          ) : agentStatus === 'paused' ? (
            <Button 
              variant="primary" 
              size="sm" 
              iconLeft={<Play className="w-4 h-4" />}
              onClick={() => setAgentStatus('running')}
            >
              Resume
            </Button>
          ) : null}
          
          {(agentStatus === 'completed' || agentStatus === 'paused' || agentStatus === 'error') && (
            <Button 
              variant="secondary" 
              size="sm" 
              iconLeft={<RotateCcw className="w-4 h-4" />}
              onClick={handleResetCampaign}
            >
              Reset
            </Button>
          )}
        </div>
      }
    >
      {/* Tab Navigation */}
      <div className="border-b border-border mb-6">
        <nav className="flex space-x-8">
          {tabs.map((tab) => {
            const IconComponent = tab.icon;
            return (
              <button
                key={tab.id}
                className={cn(
                  "flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm",
                  activeTab === tab.id
                    ? "border-accent-cyan text-accent-cyan"
                    : "border-transparent text-text-secondary hover:text-text-primary hover:border-border"
                )}
                onClick={() => setActiveTab(tab.id)}
              >
                <IconComponent className="w-4 h-4" />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Campaign Status Card */}
            <Card>
              <CardHeader
                title="Campaign Status"
                description="Current state of your business development campaign"
              />
              <CardContent>
                <div className="flex items-center gap-3 mb-4">
                  <Activity className={cn(
                    "w-5 h-5",
                    agentStatus === 'running' && 'text-success',
                    agentStatus === 'paused' && 'text-warning',
                    agentStatus === 'completed' && 'text-primary',
                    agentStatus === 'error' && 'text-error',
                    agentStatus === 'idle' && 'text-text-muted'
                  )} />
                  <span className="font-medium capitalize">{agentStatus}</span>
                </div>
                
                <div className="mb-2 flex justify-between text-sm">
                  <span>Progress</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full bg-surface rounded-full h-2">
                  <div 
                    className="bg-primary h-2 rounded-full transition-all duration-300" 
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                
                <div className="mt-4 text-sm">
                  <p className="text-text-secondary">Current Phase:</p>
                  <p className="font-medium">{currentPhase}</p>
                </div>
              </CardContent>
            </Card>
            
            {/* Target Settings Card */}
            <Card>
              <CardHeader
                title="Target Settings"
                description="Your campaign parameters"
              />
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <MapPin className="w-4 h-4 text-text-secondary" />
                      <span className="text-sm font-medium text-text-secondary">Geographic Focus</span>
                    </div>
                    <p className="text-sm">{campaignSettings.targetGeography}</p>
                  </div>
                  
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <Building className="w-4 h-4 text-text-secondary" />
                      <span className="text-sm font-medium text-text-secondary">Industries</span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {campaignSettings.targetIndustries.map((industry, index) => (
                        <Badge key={index} variant="outline" size="sm">
                          {industry}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 pt-2">
                    <div>
                      <span className="text-xs text-text-secondary">Duration</span>
                      <p className="text-sm font-medium">{campaignSettings.campaignDuration} days</p>
                    </div>
                    <div>
                      <span className="text-xs text-text-secondary">Daily Limit</span>
                      <p className="text-sm font-medium">{campaignSettings.dailyOutreachLimit} contacts</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            {/* Campaign Metrics Card */}
            <Card>
              <CardHeader
                title="Campaign Metrics"
                description="Real-time performance indicators"
              />
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div className="text-center p-3 bg-surface rounded-lg">
                    <div className="text-2xl font-bold text-primary">{metrics.leadsGenerated}</div>
                    <div className="text-xs text-text-secondary">Leads Generated</div>
                  </div>
                  <div className="text-center p-3 bg-surface rounded-lg">
                    <div className="text-2xl font-bold text-success">{metrics.qualifiedLeads}</div>
                    <div className="text-xs text-text-secondary">Qualified Leads</div>
                  </div>
                  <div className="text-center p-3 bg-surface rounded-lg">
                    <div className="text-2xl font-bold text-warning">{metrics.meetingsScheduled}</div>
                    <div className="text-xs text-text-secondary">Meetings Scheduled</div>
                  </div>
                  <div className="text-center p-3 bg-surface rounded-lg">
                    <div className="text-2xl font-bold text-error">{metrics.dealsClosed}</div>
                    <div className="text-xs text-text-secondary">Deals Closed</div>
                  </div>
                </div>
                
                <div className="mt-4 pt-4 border-t border-border">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-text-secondary">Projected Revenue</span>
                    <span className="font-bold text-lg">${metrics.revenueProjected.toLocaleString()}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
          
          {/* Campaign Phases Card */}
          <Card>
            <CardHeader
              title="Campaign Phases"
              description="Step-by-step execution of your business development strategy"
            />
            <CardContent>
              <div className="space-y-4">
                {[
                  { id: 'research', name: 'Market Research', description: 'Identify high-value prospects in Indiana SMB market' },
                  { id: 'content', name: 'Content Creation', description: 'Create personalized outreach content for each prospect' },
                  { id: 'outreach', name: 'Outreach Execution', description: 'Execute multi-channel outreach campaign' },
                  { id: 'qualification', name: 'Lead Qualification', description: 'Qualify leads using BANT framework' },
                  { id: 'proposal', name: 'Proposal Development', description: 'Create compelling proposals and close deals' },
                  { id: 'analysis', name: 'Metrics Analysis', description: 'Analyze performance and optimize strategies' }
                ].map((phase, index) => (
                  <div 
                    key={phase.id} 
                    className={cn(
                      "flex items-start gap-3 p-3 rounded-lg border",
                      currentPhase === phase.name ? 'border-primary bg-primary/5' : 'border-border'
                    )}
                  >
                    <div className={cn(
                      "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold",
                      currentPhase === phase.name ? 'bg-primary text-white' : 
                      progress >= (index / 6) * 100 ? 'bg-success text-white' : 'bg-surface text-text-secondary'
                    )}>
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <h4 className="font-medium">{phase.name}</h4>
                      <p className="text-sm text-text-secondary">{phase.description}</p>
                    </div>
                    {currentPhase === phase.name && (
                      <Badge variant="cyan" size="sm">In Progress</Badge>
                    )}
                    {progress >= ((index + 1) / 6) * 100 && (
                      <Badge variant="success" size="sm">Completed</Badge>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Configuration Tab */}
      {activeTab === 'configuration' && (
        <div className="space-y-6">
          <Card>
            <CardHeader
              title="Campaign Configuration"
              description="Configure your business development parameters"
            />
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="text-sm font-medium text-text-secondary mb-1 block">Geographic Focus</label>
                  <Input 
                    value={campaignSettings.targetGeography} 
                    onChange={(e) => setCampaignSettings({...campaignSettings, targetGeography: e.target.value})}
                    disabled={agentStatus !== 'idle'}
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium text-text-secondary mb-1 block">Campaign Duration (days)</label>
                  <Input 
                    type="number"
                    value={campaignSettings.campaignDuration} 
                    onChange={(e) => setCampaignSettings({...campaignSettings, campaignDuration: parseInt(e.target.value) || 30})}
                    disabled={agentStatus !== 'idle'}
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium text-text-secondary mb-1 block">Daily Outreach Limit</label>
                  <Input 
                    type="number"
                    value={campaignSettings.dailyOutreachLimit} 
                    onChange={(e) => setCampaignSettings({...campaignSettings, dailyOutreachLimit: parseInt(e.target.value) || 10})}
                    disabled={agentStatus !== 'idle'}
                  />
                </div>
                
                <div>
                  <label className="text-sm font-medium text-text-secondary mb-1 block">Budget Per Lead ($)</label>
                  <Input 
                    type="number"
                    value={campaignSettings.budgetPerLead} 
                    onChange={(e) => setCampaignSettings({...campaignSettings, budgetPerLead: parseInt(e.target.value) || 50})}
                    disabled={agentStatus !== 'idle'}
                  />
                </div>
              </div>
              
              <div className="mt-6">
                <label className="text-sm font-medium text-text-secondary mb-1 block">Target Industries</label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {['Healthcare', 'Manufacturing', 'Legal', 'Agriculture', 'Professional Services', 'Retail', 'Education'].map(industry => (
                    <div key={industry} className="flex items-center space-x-2">
                      <input
                        type="checkbox"
                        id={industry}
                        checked={campaignSettings.targetIndustries.includes(industry)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setCampaignSettings({
                              ...campaignSettings,
                              targetIndustries: [...campaignSettings.targetIndustries, industry]
                            });
                          } else {
                            setCampaignSettings({
                              ...campaignSettings,
                              targetIndustries: campaignSettings.targetIndustries.filter(i => i !== industry)
                            });
                          }
                        }}
                        disabled={agentStatus !== 'idle'}
                        className="rounded border-border text-accent-cyan focus:ring-accent-cyan"
                      />
                      <label htmlFor={industry} className="text-sm">{industry}</label>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="mt-6">
                <label className="text-sm font-medium text-text-secondary mb-1 block">Service Focus</label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {[
                    { id: 'software', label: 'Custom Software Solutions', icon: Code },
                    { id: 'website', label: 'Website Design & Development', icon: Globe },
                    { id: 'ai', label: 'AI Integration Services', icon: Bot }
                  ].map(service => {
                    const IconComponent = service.icon;
                    return (
                      <div key={service.id} className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          id={service.id}
                          checked={campaignSettings.serviceFocus.includes(service.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setCampaignSettings({
                                ...campaignSettings,
                                serviceFocus: [...campaignSettings.serviceFocus, service.id]
                              });
                            } else {
                              setCampaignSettings({
                                ...campaignSettings,
                                serviceFocus: campaignSettings.serviceFocus.filter(s => s !== service.id)
                              });
                            }
                          }}
                          disabled={agentStatus !== 'idle'}
                          className="rounded border-border text-accent-cyan focus:ring-accent-cyan"
                        />
                        <label htmlFor={service.id} className="text-sm flex items-center gap-1">
                          <IconComponent className="w-4 h-4" />
                          {service.label}
                        </label>
                      </div>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Results Tab */}
      {activeTab === 'results' && (
        <div className="space-y-6">
          {agentStatus === 'completed' ? (
            <Card>
              <CardHeader
                title="Campaign Results"
                description="Detailed outcomes from your business development campaign"
              />
              <CardContent>
                <div className="prose max-w-none">
                  <h3 className="text-lg font-semibold mb-2">Summary</h3>
                  <p className="text-text-secondary mb-4">
                    Your Indiana SMB Business Development campaign has completed successfully. 
                    The agent identified <strong>{metrics.leadsGenerated}</strong> potential prospects, qualified <strong>{metrics.qualifiedLeads}</strong> leads, 
                    scheduled <strong>{metrics.meetingsScheduled}</strong> meetings, and closed <strong>{metrics.dealsClosed}</strong> deals.
                  </p>
                  
                  <h3 className="text-lg font-semibold mb-2">Top Performing Industries</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                    <div className="p-3 bg-success/10 border border-success/20 rounded-lg">
                      <div className="text-success font-bold">Healthcare</div>
                      <div className="text-sm text-text-secondary">12 qualified leads</div>
                    </div>
                    <div className="p-3 bg-success/10 border border-success/20 rounded-lg">
                      <div className="text-success font-bold">Manufacturing</div>
                      <div className="text-sm text-text-secondary">8 qualified leads</div>
                    </div>
                    <div className="p-3 bg-success/10 border border-success/20 rounded-lg">
                      <div className="text-success font-bold">Professional Services</div>
                      <div className="text-sm text-text-secondary">3 qualified leads</div>
                    </div>
                  </div>
                  
                  <h3 className="text-lg font-semibold mb-2 mt-4">Recommendations</h3>
                  <ul className="list-disc pl-5 space-y-1 text-text-secondary">
                    <li>Follow up with the {metrics.qualifiedLeads - metrics.meetingsScheduled} qualified leads who didn&apos;t schedule meetings</li>
                    <li>Develop case studies from the {metrics.dealsClosed} closed deals to strengthen future proposals</li>
                    <li>Refine targeting based on which industries showed the highest conversion rates</li>
                    <li>Scale successful outreach strategies to increase lead generation</li>
                  </ul>
                  
                  <h3 className="text-lg font-semibold mb-2 mt-4">Next Steps</h3>
                  <ol className="list-decimal pl-5 space-y-1 text-text-secondary">
                    <li>Begin implementation of projects from closed deals</li>
                    <li>Initiate follow-up campaigns with nurtured prospects</li>
                    <li>Adjust campaign parameters based on performance metrics</li>
                    <li>Schedule next campaign cycle</li>
                  </ol>
                </div>
              </CardContent>
              <CardFooter>
                <Button 
                  variant="primary" 
                  iconLeft={<Play className="w-4 h-4" />}
                  onClick={handleStartCampaign}
                >
                  Start New Campaign
                </Button>
              </CardFooter>
            </Card>
          ) : agentStatus === 'idle' ? (
            <Card>
              <CardHeader
                title="Campaign Ready"
                description="Configure your campaign and start business development"
              />
              <CardContent>
                <div className="text-center py-8">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-surface flex items-center justify-center">
                    <Target className="w-8 h-8 text-text-muted" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Ready to Start Campaign</h3>
                  <p className="text-text-secondary mb-6">
                    Configure your campaign parameters and launch your business development initiative
                  </p>
                  <Button 
                    variant="primary" 
                    iconLeft={<Play className="w-4 h-4" />}
                    onClick={handleStartCampaign}
                  >
                    Start Campaign
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader
                title="Campaign in Progress"
                description="Monitor your business development campaign"
              />
              <CardContent>
                <div className="text-center py-8">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-surface flex items-center justify-center">
                    <Activity className="w-8 h-8 text-text-muted animate-pulse" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">Campaign Running</h3>
                  <p className="text-text-secondary mb-6">
                    Your business development campaign is currently executing. Monitor progress in the dashboard.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          <Card>
            <CardHeader
              title="Performance Analytics"
              description="Detailed metrics and insights from your campaign"
            />
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                <div className="p-4 bg-surface rounded-lg">
                  <div className="text-2xl font-bold text-primary">{metrics.leadsGenerated}</div>
                  <div className="text-sm text-text-secondary">Total Leads</div>
                  <div className="text-xs text-success mt-1">↑ 15% from last campaign</div>
                </div>
                <div className="p-4 bg-surface rounded-lg">
                  <div className="text-2xl font-bold text-success">{Math.round((metrics.qualifiedLeads / metrics.leadsGenerated) * 100)}%</div>
                  <div className="text-sm text-text-secondary">Qualification Rate</div>
                  <div className="text-xs text-success mt-1">↑ 8% from last campaign</div>
                </div>
                <div className="p-4 bg-surface rounded-lg">
                  <div className="text-2xl font-bold text-warning">{Math.round((metrics.meetingsScheduled / metrics.qualifiedLeads) * 100)}%</div>
                  <div className="text-sm text-text-secondary">Meeting Rate</div>
                  <div className="text-xs text-warning mt-1">↓ 3% from last campaign</div>
                </div>
                <div className="p-4 bg-surface rounded-lg">
                  <div className="text-2xl font-bold text-error">{Math.round((metrics.dealsClosed / metrics.meetingsScheduled) * 100)}%</div>
                  <div className="text-sm text-text-secondary">Close Rate</div>
                  <div className="text-xs text-success mt-1">↑ 12% from last campaign</div>
                </div>
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card>
                  <CardHeader
                    title="Channel Performance"
                    description="Outreach effectiveness by channel"
                  />
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Email Outreach</span>
                          <span>78%</span>
                        </div>
                        <div className="w-full bg-surface rounded-full h-2">
                          <div className="bg-primary h-2 rounded-full" style={{ width: '78%' }}></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>LinkedIn Messages</span>
                          <span>65%</span>
                        </div>
                        <div className="w-full bg-surface rounded-full h-2">
                          <div className="bg-success h-2 rounded-full" style={{ width: '65%' }}></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Phone Calls</span>
                          <span>42%</span>
                        </div>
                        <div className="w-full bg-surface rounded-full h-2">
                          <div className="bg-warning h-2 rounded-full" style={{ width: '42%' }}></div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
                
                <Card>
                  <CardHeader
                    title="Industry Conversion"
                    description="Performance by target industry"
                  />
                  <CardContent>
                    <div className="space-y-3">
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Healthcare</span>
                          <span>32%</span>
                        </div>
                        <div className="w-full bg-surface rounded-full h-2">
                          <div className="bg-primary h-2 rounded-full" style={{ width: '32%' }}></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Manufacturing</span>
                          <span>28%</span>
                        </div>
                        <div className="w-full bg-surface rounded-full h-2">
                          <div className="bg-success h-2 rounded-full" style={{ width: '28%' }}></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Professional Services</span>
                          <span>22%</span>
                        </div>
                        <div className="w-full bg-surface rounded-full h-2">
                          <div className="bg-warning h-2 rounded-full" style={{ width: '22%' }}></div>
                        </div>
                      </div>
                      <div>
                        <div className="flex justify-between text-sm mb-1">
                          <span>Legal</span>
                          <span>18%</span>
                        </div>
                        <div className="w-full bg-surface rounded-full h-2">
                          <div className="bg-error h-2 rounded-full" style={{ width: '18%' }}></div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </AppShell>
  );
}


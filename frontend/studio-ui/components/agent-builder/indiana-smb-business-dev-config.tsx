import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

interface BusinessDevConfig {
  targetIndustries: string[];
  targetGeography: string;
  campaignDuration: number;
  dailyOutreachLimit: number;
  budgetPerLead: number;
  serviceFocus: ('software' | 'website' | 'ai')[];
  outreachChannels: ('email' | 'linkedin' | 'phone')[];
}

interface BusinessDevAgentUIProps {
  onRun: (config: BusinessDevConfig) => void;
  isRunning: boolean;
}

export default function BusinessDevAgentUI({ onRun, isRunning }: BusinessDevAgentUIProps) {
  const [config, setConfig] = useState<BusinessDevConfig>({
    targetIndustries: ['Healthcare', 'Manufacturing', 'Legal'],
    targetGeography: 'Indiana (Brown County, Columbus, Bloomington, Indianapolis, 100-mile radius)',
    campaignDuration: 30,
    dailyOutreachLimit: 10,
    budgetPerLead: 50,
    serviceFocus: ['software', 'website'],
    outreachChannels: ['email', 'linkedin']
  });

  const handleIndustryChange = (industry: string, checked: boolean) => {
    if (checked) {
      setConfig(prev => ({
        ...prev,
        targetIndustries: [...prev.targetIndustries, industry]
      }));
    } else {
      setConfig(prev => ({
        ...prev,
        targetIndustries: prev.targetIndustries.filter(i => i !== industry)
      }));
    }
  };

  const handleServiceChange = (service: 'software' | 'website' | 'ai', checked: boolean) => {
    if (checked) {
      setConfig(prev => ({
        ...prev,
        serviceFocus: [...prev.serviceFocus, service]
      }));
    } else {
      setConfig(prev => ({
        ...prev,
        serviceFocus: prev.serviceFocus.filter(s => s !== service)
      }));
    }
  };

  const handleChannelChange = (channel: 'email' | 'linkedin' | 'phone', checked: boolean) => {
    if (checked) {
      setConfig(prev => ({
        ...prev,
        outreachChannels: [...prev.outreachChannels, channel]
      }));
    } else {
      setConfig(prev => ({
        ...prev,
        outreachChannels: prev.outreachChannels.filter(c => c !== channel)
      }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onRun(config);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Target Market Configuration</CardTitle>
          <CardDescription>Define your target industries and geographic focus</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div>
            <Label htmlFor="geography">Target Geography</Label>
            <Input
              id="geography"
              value={config.targetGeography}
              onChange={(e) => setConfig({...config, targetGeography: e.target.value})}
              placeholder="Enter target geographic area"
            />
          </div>

          <div>
            <Label>Target Industries</Label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mt-2">
              {['Healthcare', 'Manufacturing', 'Legal', 'Agriculture', 'Professional Services', 'Retail', 'Education'].map(industry => (
                <div key={industry} className="flex items-center space-x-2">
                  <Checkbox
                    id={industry}
                    checked={config.targetIndustries.includes(industry)}
                    onCheckedChange={(checked) => handleIndustryChange(industry, checked as boolean)}
                  />
                  <Label htmlFor={industry}>{industry}</Label>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Service Focus</CardTitle>
          <CardDescription>Select the services you want to promote</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-2">
              <Checkbox
                id="software"
                checked={config.serviceFocus.includes('software')}
                onCheckedChange={(checked) => handleServiceChange('software', checked as boolean)}
              />
              <Label htmlFor="software">Custom Software Solutions</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="website"
                checked={config.serviceFocus.includes('website')}
                onCheckedChange={(checked) => handleServiceChange('website', checked as boolean)}
              />
              <Label htmlFor="website">Website Design & Development</Label>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="ai"
                checked={config.serviceFocus.includes('ai')}
                onCheckedChange={(checked) => handleServiceChange('ai', checked as boolean)}
              />
              <Label htmlFor="ai">AI Integration Services</Label>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Outreach Strategy</CardTitle>
          <CardDescription>Configure your outreach channels and cadence</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="duration">Campaign Duration (days)</Label>
              <Input
                id="duration"
                type="number"
                value={config.campaignDuration}
                onChange={(e) => setConfig({...config, campaignDuration: parseInt(e.target.value) || 30})}
                min="7"
                max="90"
              />
            </div>
            <div>
              <Label htmlFor="dailyLimit">Daily Outreach Limit</Label>
              <Input
                id="dailyLimit"
                type="number"
                value={config.dailyOutreachLimit}
                onChange={(e) => setConfig({...config, dailyOutreachLimit: parseInt(e.target.value) || 10})}
                min="1"
                max="50"
              />
            </div>
            <div>
              <Label htmlFor="budgetPerLead">Budget Per Lead ($)</Label>
              <Input
                id="budgetPerLead"
                type="number"
                value={config.budgetPerLead}
                onChange={(e) => setConfig({...config, budgetPerLead: parseInt(e.target.value) || 50})}
                min="10"
                max="500"
              />
            </div>
          </div>

          <div>
            <Label>Outreach Channels</Label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-2">
              {['Email', 'LinkedIn', 'Phone'].map(channel => (
                <div key={channel} className="flex items-center space-x-2">
                  <Checkbox
                    id={channel.toLowerCase()}
                    checked={config.outreachChannels.includes(channel.toLowerCase() as any)}
                    onCheckedChange={(checked) => handleChannelChange(channel.toLowerCase() as any, checked as boolean)}
                  />
                  <Label htmlFor={channel.toLowerCase()}>{channel}</Label>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button type="submit" disabled={isRunning}>
          {isRunning ? 'Running Campaign...' : 'Start Business Development Campaign'}
        </Button>
      </div>
    </form>
  );
}
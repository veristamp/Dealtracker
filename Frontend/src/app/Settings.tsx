import { useState, useEffect } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Play, Pause, Settings as SettingsIcon, Clock, FolderSync as Sync, Volume2, VolumeX } from 'lucide-react';
import { api } from '@/api';
import { toast } from 'sonner';
import { useStore } from '@/store/useStore'; // 1. Import useStore
import { Switch } from '@/components/ui/switch'; // 2. Import Switch

export default function Settings() {
  const { isSoundEnabled, setIsSoundEnabled } = useStore(); // 3. Get state and action from store
  const [schedulerStatus, setSchedulerStatus] = useState<{ running: boolean }>({ running: false });
  const [interval, setInterval] = useState<number>(10);
  const [newInterval, setNewInterval] = useState<string>('10');
  const [isLoading, setIsLoading] = useState(false);

  // ... (all existing functions like fetchSchedulerStatus, handleStopScheduler, etc. remain unchanged)

    const fetchSchedulerStatus = async () => {
    try {
      const response = await api.getSchedulerStatus();
      if (response.success && response.data) {
        setSchedulerStatus(response.data);
      }
    } catch (error) {
      console.error('Failed to fetch scheduler status:', error);
    }
  };

  const fetchInterval = async () => {
    try {
      const response = await api.getSchedulerInterval();
      if (response.success && response.data) {
        setInterval(response.data.interval);
        setNewInterval(response.data.interval.toString());
      }
    } catch (error) {
      console.error('Failed to fetch interval:', error);
    }
  };

  useEffect(() => {
    fetchSchedulerStatus();
    fetchInterval();
  }, []);

  const handleStartScheduler = async () => {
    setIsLoading(true);
    try {
      const response = await api.startScheduler();
      if (response.success) {
        toast.success('Scheduler started successfully');
        await fetchSchedulerStatus();
      } else {
        toast.error(response.message || 'Failed to start scheduler');
      }
    } catch (error) {
      toast.error('An error occurred while starting the scheduler');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopScheduler = async () => {
    setIsLoading(true);
    try {
      const response = await api.stopScheduler();
      if (response.success) {
        toast.success('Scheduler stopped successfully');
        await fetchSchedulerStatus();
      } else {
        toast.error(response.message || 'Failed to stop scheduler');
      }
    } catch (error) {
      toast.error('An error occurred while stopping the scheduler');
    } finally {
      setIsLoading(false);
    }
  };
    
  const handleUpdateInterval = async () => {
    const intervalValue = parseInt(newInterval);
    if (isNaN(intervalValue) || intervalValue < 1) {
      toast.error('Please enter a valid interval (minimum 1 minute)');
      return;
    }

    setIsLoading(true);
    try {
      // Corrected to call the right API method as per api/index.ts
      const response = await api.rescheduleScheduler(intervalValue);
      if (response.success) {
        toast.success(`Scraping interval updated to ${intervalValue} minutes`);
        await fetchInterval();
      } else {
        toast.error(response.message || 'Failed to update interval');
      }
    } catch (error) {
      toast.error('An error occurred while updating the interval');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSyncProducts = async () => {
    setIsLoading(true);
    try {
      const response = await api.syncProducts();
      if (response.success) {
        toast.success('Products synchronized successfully');
      } else {
        toast.error(response.message || 'Failed to sync products');
      }
    } catch (error) {
      toast.error('An error occurred during synchronization');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Settings" 
        description="Configure system settings and automation controls"
      />

      {/* System Status Card (Unchanged) */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <SettingsIcon className="h-5 w-5" />
            <span>System Status</span>
          </CardTitle>
          <CardDescription>
            Monitor and control the scraping scheduler
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="font-medium">Scheduler Status</p>
              <p className="text-sm text-muted-foreground">
                The automated price checking system
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Badge variant={schedulerStatus.running ? 'default' : 'secondary'}>
                {schedulerStatus.running ? 'Running' : 'Stopped'}
              </Badge>
              {schedulerStatus.running ? (
                <Button variant="outline" size="sm" onClick={handleStopScheduler} disabled={isLoading}>
                  <Pause className="mr-2 h-4 w-4" /> Stop
                </Button>
              ) : (
                <Button size="sm" onClick={handleStartScheduler} disabled={isLoading}>
                  <Play className="mr-2 h-4 w-4" /> Start
                </Button>
              )}
            </div>
          </div>
          <Separator />
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Clock className="h-4 w-4" />
                <Label>Scraping Interval</Label>
              </div>
              <p className="text-sm text-muted-foreground">
                How often the system checks for price changes (in minutes)
              </p>
              <div className="flex items-center space-x-2">
                <Input type="number" value={newInterval} onChange={(e) => setNewInterval(e.target.value)} placeholder="Enter interval" className="w-32" min="1"/>
                <span className="text-sm text-muted-foreground">minutes</span>
                <Button variant="outline" onClick={handleUpdateInterval} disabled={isLoading || newInterval === interval.toString()}>
                  Update
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Current interval: {interval} minutes
              </p>
            </div>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="font-medium">Manual Sync</p>
              <p className="text-sm text-muted-foreground">
                Synchronize products with the server manually
              </p>
            </div>
            <Button variant="outline" onClick={handleSyncProducts} disabled={isLoading}>
              <Sync className="mr-2 h-4 w-4" /> Sync Now
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Application Settings Card (Updated) */}
      <Card>
        <CardHeader>
          <CardTitle>Application Settings</CardTitle>
          <CardDescription>
            General application preferences and configurations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="font-medium">Theme</p>
              <p className="text-sm text-muted-foreground">
                Toggle between light and dark mode using the button in the sidebar
              </p>
            </div>
            <Badge variant="outline">Auto-detected</Badge>
          </div>
          <Separator />
          {/* 4. Add the new Notification Sound setting */}
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="font-medium">Notification Sound</p>
              <p className="text-sm text-muted-foreground">
                Play a sound when a new price drop alert arrives
              </p>
            </div>
            <div className="flex items-center space-x-2">
              {isSoundEnabled ? <Volume2 className="h-5 w-5 text-muted-foreground" /> : <VolumeX className="h-5 w-5 text-muted-foreground" />}
              <Switch
                checked={isSoundEnabled}
                onCheckedChange={setIsSoundEnabled}
                aria-label="Toggle notification sounds"
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
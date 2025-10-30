import { useEffect, useState, useRef } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { StatsCard } from '@/components/common/StatsCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Package, TrendingDown, Activity, Clock, Play, Pause, Settings } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { api } from '@/api';
import { formatTimestamp, cn } from '@/lib/utils';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { Alert as AlertType } from '@/lib/types';

type AnimatedAlert = AlertType & { 
  animation: 'new' | 'exiting' | 'none';
  isRemoving?: boolean;
};

const tierColors: { [key: string]: string } = {
  bronze: 'bg-yellow-800/20 text-yellow-500 border-yellow-700/30 dark:bg-yellow-700/10 dark:text-yellow-600 dark:border-yellow-700/20',
  silver: 'bg-slate-500/20 text-slate-600 border-slate-500/30 dark:bg-slate-400/10 dark:text-slate-400 dark:border-slate-400/20',
  gold: 'bg-amber-500/20 text-amber-600 border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-500 dark:border-amber-500/20',
};

export default function Dashboard() {
  const { 
    dashboardStats, 
    setDashboardStats, 
    alerts,
    setAlerts,
    user,
    isSoundEnabled,
  } = useStore();

  const [animatedAlerts, setAnimatedAlerts] = useState<AnimatedAlert[]>([]);
  const previousAlertsRef = useRef<AlertType[]>([]);
  const audioRef = useRef<HTMLAudioElement>(null);
  const isInitialLoadRef = useRef(true);
  
  const [schedulerStatus, setSchedulerStatus] = useState({ running: false });
  const [interval, setIntervalValue] = useState(10);
  const [newInterval, setNewInterval] = useState('10');
  const [isLoading, setIsLoading] = useState(false);

  // EFFECT 1: Initial data load
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        const [statsRes, statusRes, intervalRes, alertsRes] = await Promise.all([
          api.getDashboardStats(),
          api.getSchedulerStatus(),
          api.getSchedulerInterval(),
          api.getAlerts(),
        ]);

        if (statsRes.success && statsRes.data) setDashboardStats(statsRes.data);
        if (statusRes.success && statusRes.data) setSchedulerStatus(statusRes.data);
        if (intervalRes.success && intervalRes.data) {
          setIntervalValue(intervalRes.data.interval);
          setNewInterval(intervalRes.data.interval.toString());
        }
        if (alertsRes.success && alertsRes.data) {
          setAlerts(alertsRes.data);
          // Mark all initial alerts as 'none' animation
          const initialAlerts: AnimatedAlert[] = alertsRes.data.map(a => ({ 
            ...a, 
            animation: 'none' as const
          }));
          setAnimatedAlerts(initialAlerts);
          previousAlertsRef.current = alertsRes.data;
          isInitialLoadRef.current = false; // Mark initial load as complete
        }
      } catch (error) {
        toast.error("Failed to load dashboard data.");
      }
    };
    fetchInitialData();
  }, []);

  // EFFECT 2: Real-time SSE listener
  useEffect(() => {
    const eventSource = new EventSource("http://127.0.0.1:8001/api/alerts/stream?token=idontthinkyoucancrackthiseverinlife:)haha");

    const handlePriceDrop = (data: any) => {
      toast.success('🎉 Price Drop!', {
        description: `${data.product_name} is now just ₹${data.scraped_price}!`,
      });
      
      // Play sound immediately when SSE event is received
      if (isSoundEnabled && audioRef.current) {
        audioRef.current.currentTime = 0; // Reset to beginning
        audioRef.current.play().catch(error => {
          console.error("Audio play failed:", error);
        });
      }
      
      // Fetch updated alerts
      api.getAlerts().then(res => {
        if (res.success && res.data) {
          setAlerts(res.data);
        }
      });
      api.getDashboardStats().then(res => {
        if (res.success && res.data) {
          setDashboardStats(res.data);
        }
      });
    };

    eventSource.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "price_drop" && msg.data) {
          handlePriceDrop(msg.data);
        }
      } catch (e) { 
        // Ignore non-JSON messages 
      }
    };

    eventSource.onerror = (error) => {
      console.error("SSE connection error, closing.", error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [isSoundEnabled]);

  // EFFECT 3: Improved Animation and Sound handler
  useEffect(() => {
    // Skip animation logic during initial load
    if (isInitialLoadRef.current) {
      return;
    }

    const prevAlerts = previousAlertsRef.current;
    const currentAlerts = alerts;

    // Create maps for efficient lookup
    const prevAlertsMap = new Map(prevAlerts.map(a => [a.id, a]));
    const currentAlertsMap = new Map(currentAlerts.map(a => [a.id, a]));

    // Find new and exiting alerts
    const newAlertIds = currentAlerts
      .filter(alert => !prevAlertsMap.has(alert.id))
      .map(alert => alert.id);
    
    const exitingAlertIds = prevAlerts
      .filter(alert => !currentAlertsMap.has(alert.id))
      .map(alert => alert.id);

    // Create the animated alerts list
    const newAnimatedAlerts: AnimatedAlert[] = [];

    // Add all current alerts (existing + new)
    currentAlerts.forEach(alert => {
      newAnimatedAlerts.push({
        ...alert,
        animation: newAlertIds.includes(alert.id) ? 'new' : 'none'
      });
    });

    // Add exiting alerts with exiting animation
    exitingAlertIds.forEach(id => {
      const exitingAlert = prevAlertsMap.get(id);
      if (exitingAlert) {
        newAnimatedAlerts.push({
          ...exitingAlert,
          animation: 'exiting',
          isRemoving: true
        });
      }
    });

    setAnimatedAlerts(newAnimatedAlerts);

    // Clean up exiting alerts after animation completes
    if (exitingAlertIds.length > 0) {
      const cleanupTimer = setTimeout(() => {
        setAnimatedAlerts(prev => 
          prev.filter(alert => !alert.isRemoving)
            .map(alert => ({
              ...alert,
              animation: 'none' // Reset all animations
            }))
        );
      }, 1200); // Match this with your CSS animation duration

      return () => clearTimeout(cleanupTimer);
    } else if (newAlertIds.length > 0) {
      // Reset new alert animations after they complete
      const resetTimer = setTimeout(() => {
        setAnimatedAlerts(prev => 
          prev.map(alert => ({
            ...alert,
            animation: 'none'
          }))
        );
      }, 1000); // Allow green glow to be visible for 1 second

      return () => clearTimeout(resetTimer);
    }

    // Update the reference for next comparison
    previousAlertsRef.current = currentAlerts;

  }, [alerts]);

  // Initialize audio for better browser compatibility
  useEffect(() => {
    const audio = audioRef.current;
    if (audio) {
      // Try to load the audio file
      audio.load();
      
      // Add event listeners for debugging
      audio.addEventListener('canplaythrough', () => {
        console.log('Audio can play through');
      });
      
      audio.addEventListener('error', (e) => {
        console.error('Audio error:', e);
      });
    }
  }, []);

  const handleToggleScheduler = async () => {
    setIsLoading(true);
    const action = schedulerStatus.running ? api.stopScheduler : api.startScheduler;
    const actionName = schedulerStatus.running ? 'stopped' : 'started';
    
    try {
      const response = await action();
      if (response.success) {
        toast.success(`Scheduler ${actionName} successfully.`);
        const statusRes = await api.getSchedulerStatus();
        if (statusRes.success && statusRes.data) setSchedulerStatus(statusRes.data);
      } else {
        toast.error(response.message || `Failed to ${actionName} scheduler.`);
      }
    } catch (error) {
      toast.error(`An error occurred while controlling the scheduler.`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateInterval = async () => {
    const intervalValue = parseInt(newInterval, 10);
    if (isNaN(intervalValue) || intervalValue < 1) {
      toast.error('Please enter a valid interval (minimum 1 minute)');
      return;
    }
    
    setIsLoading(true);
    try {
      const response = await api.rescheduleScheduler(intervalValue);
      if (response.success) {
        toast.success(`Interval updated to ${intervalValue} minutes.`);
        const intervalRes = await api.getSchedulerInterval();
        if (intervalRes.success && intervalRes.data) {
          setIntervalValue(intervalRes.data.interval);
          setNewInterval(intervalRes.data.interval.toString());
        }
      } else {
        toast.error(response.message || 'Failed to update interval.');
      }
    } catch (error) {
      toast.error('An error occurred while updating interval.');
    } finally {
      setIsLoading(false);
    }
  };

  const userTier = user?.tier || 'bronze';
  const tierBadge = (
    <Badge variant="outline" className={cn("capitalize text-base font-semibold", tierColors[userTier])}>
      {userTier}
    </Badge>
  );

  return (
    <div className="space-y-6">
      <audio 
        ref={audioRef} 
        src="/sounds/notification.mp3" 
        preload="auto"
        // Add these attributes for better browser support
        crossOrigin="anonymous"
      />
      
      <PageHeader 
        title="Dashboard" 
        description="Live activity feed and system overview" 
        badge={tierBadge} 
      />
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <StatsCard 
          title="Total Products" 
          value={dashboardStats?.total_products || 0} 
          description="Products being tracked" 
          icon={Package} 
        />
        <StatsCard 
          title="Active Deals" 
          value={dashboardStats?.active_deals || 0} 
          description="Products with price drops" 
          icon={TrendingDown} 
        />
        <StatsCard 
          title="Recent Alerts" 
          value={alerts.length} 
          description="Notifications for price drops" 
          icon={Activity} 
        />
        <StatsCard 
          title="System Status" 
          value={schedulerStatus.running ? 'Running' : 'Stopped'} 
          description={`Checks prices every ${interval} min.`} 
          icon={Clock}
        >
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" size="sm" className="w-full">
                <Settings className="mr-2 h-4 w-4" /> Manage
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-80" align="end">
              <div className="grid gap-4">
                <div className="space-y-2">
                  <h4 className="font-medium leading-none">System Control</h4>
                  <p className="text-sm text-muted-foreground">Start or stop the price scraper.</p>
                </div>
                <Button 
                  onClick={handleToggleScheduler} 
                  disabled={isLoading} 
                  size="lg" 
                  className="w-full"
                >
                  {schedulerStatus.running ? (
                    <>
                      <Pause className="mr-2 h-4 w-4" /> Stop System
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" /> Start System
                    </>
                  )}
                </Button>
                <div className="grid gap-2">
                  <Label htmlFor="interval">Scraping Interval (min)</Label>
                  <div className="flex items-center space-x-2">
                    <Input 
                      id="interval" 
                      type="number" 
                      value={newInterval} 
                      onChange={(e) => setNewInterval(e.target.value)} 
                      className="flex-1" 
                      min="1" 
                    />
                    <Button 
                      variant="outline" 
                      onClick={handleUpdateInterval} 
                      disabled={isLoading || newInterval === interval.toString()}
                    >
                      Update
                    </Button>
                  </div>
                </div>
              </div>
            </PopoverContent>
          </Popover>
        </StatsCard>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>Recent Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {animatedAlerts.length > 0 ? (
              animatedAlerts
                .sort((a, b) => {
                  // Sort by animation state first, then by timestamp
                  if (a.animation === 'new' && b.animation !== 'new') return -1;
                  if (b.animation === 'new' && a.animation !== 'new') return 1;
                  return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime();
                })
                .map((alert) => (
                  <div 
                    key={`${alert.id}-${alert.isRemoving ? 'removing' : 'normal'}`}
                    className={cn(
                      "flex items-center justify-between p-4 border rounded-lg transition-all duration-500",
                      alert.animation === 'new' && 'animate-glow-green',
                      alert.animation === 'exiting' && 'animate-glow-red-and-fade'
                    )}
                  >
                    <div className="space-y-1">
                      <div className="font-medium">{alert.product_name}</div>
                      <div className="text-sm text-muted-foreground">
                        Price dropped to ₹{alert.scraped_price.toLocaleString()} 
                        (target: ₹{alert.threshold_price.toLocaleString()})
                      </div>
                    </div>
                    <div className="text-right text-xs text-muted-foreground">
                      {formatTimestamp(alert.timestamp)}
                    </div>
                  </div>
                ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <p>No price drop alerts yet.</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

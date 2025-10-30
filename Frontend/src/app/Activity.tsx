// src/app/Activity.tsx (Updated)

import { useState, useEffect } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { api } from '@/api';
import { type ActivityLog as ActivityLogType } from '@/lib/types';
import { formatTimestamp } from '@/lib/utils'; // 1. Import the new function
import { PackagePlus, Trash2, SlidersHorizontal } from 'lucide-react';

const activityIcons: { [key: string]: React.ElementType } = {
  PRODUCT_ADDED: PackagePlus,
  PRODUCT_REMOVED: Trash2,
  PRODUCT_REMOVED_BULK: Trash2,
  THRESHOLD_UPDATED: SlidersHorizontal,
};
const activityText: { [key: string]: (details: any) => string } = {
  PRODUCT_ADDED: details => `Added product: ${details.url}`,
  PRODUCT_REMOVED: details => `Removed product with ID: ${details.product_id}`,
  PRODUCT_REMOVED_BULK: details => `Bulk deleted ${details.count} products.`,
  THRESHOLD_UPDATED: details => `Updated price threshold for product ID: ${details.product_id}`,
};
export default function Activity() {
  const [logs, setLogs] = useState<ActivityLogType[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  useEffect(() => {
    setIsLoading(true);
    api.getActivity()
      .then(response => {
        if (response.success && Array.isArray(response.data)) {
          setLogs(response.data);
        }
      })
      .catch(error => {
        console.error("Failed to fetch activity logs:", error);
      })
      .finally(() => {
        setIsLoading(false);
       });
  }, []);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Activity Log"
        description="A timeline of recent events and actions in the application."
      />
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {isLoading ? (
              <>
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
                <Skeleton className="h-12 w-full" />
              </>
            ) : logs.length > 0 ? (
              logs.map((log) => {
                const Icon = activityIcons[log.action_type] || Activity;
                const text = activityText[log.action_type] 
                  ? activityText[log.action_type](log.details) 
                  : `Unknown action: ${log.action_type}`;

                return (
                  <div key={log.id} className="flex items-start space-x-4">
                    <div className="flex-shrink-0">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted">
                        <Icon className="h-5 w-5 text-muted-foreground" />
                      </div>
                    </div>
                    <div className="flex-1 pt-1">
                       <p className="font-medium text-sm">{text}</p>
                      <p className="text-xs text-muted-foreground">
                        {/* 2. Use the new function here */}
                        {formatTimestamp(log.timestamp)}
                      </p>
                    </div>
                  </div>
                );
              })
            ) : (
              <Alert>
                <AlertDescription>No activity has been logged yet.</AlertDescription>
              </Alert>
            )}
          </div>
        </CardContent>
      </Card>
     </div>
  );
}
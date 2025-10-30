// src/components/common/StatsCard.tsx

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { type LucideIcon } from 'lucide-react';
import { ReactNode } from 'react'; // Import ReactNode

interface StatsCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: LucideIcon;
  children?: ReactNode; // Add children prop
}

export function StatsCard({ title, value, description, icon: Icon, children }: StatsCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground">{description}</p>
        )}
        {/* Render children if they exist */}
        {children && <div className="mt-4">{children}</div>}
      </CardContent>
    </Card>
  );
}
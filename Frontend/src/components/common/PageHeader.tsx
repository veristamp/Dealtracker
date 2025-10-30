// src/components/common/PageHeader.tsx (Updated)

import { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  description?: string;
  children?: ReactNode;
  badge?: ReactNode; // 1. Add badge prop
}

export function PageHeader({ title, description, children, badge }: PageHeaderProps) {
  return (
    <div className="flex items-center justify-between py-6">
      <div className="space-y-1">
        {/* 2. Create a flex container for the title and badge */}
        <div className="flex items-center gap-x-3">
          <h2 className="text-2xl font-bold tracking-tight">{title}</h2>
          {badge}
        </div>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {children}
    </div>
  );
}
// src/components/products/columns.tsx

import { ColumnDef } from '@tanstack/react-table';
import { Product } from '@/lib/types';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { MoreHorizontal, Edit, Trash2, ExternalLink } from 'lucide-react';
import { formatTimestamp } from '@/lib/utils';
import { Switch } from '@/components/ui/switch';

// Props now include the onToggleStatus handler
interface ColumnsProps {
  onEdit: (product: Product) => void;
  onDelete: (product: Product) => void;
  onToggleStatus: (productId: number, newStatus: boolean) => void;
}

export const createColumns = ({ onEdit, onDelete, onToggleStatus }: ColumnsProps): ColumnDef<Product>[] => [
  {
    id: 'select',
    header: ({ table }) => (
      <Checkbox
        checked={table.getIsAllPageRowsSelected() || (table.getIsSomePageRowsSelected() && 'indeterminate')}
        onCheckedChange={(value) => table.toggleAllPageRowsSelected(!!value)}
        aria-label="Select all"
      />
    ),
    cell: ({ row }) => (
      <Checkbox
        checked={row.getIsSelected()}
        onCheckedChange={(value) => row.toggleSelected(!!value)}
        aria-label="Select row"
      />
    ),
    enableSorting: false,
    enableHiding: false,
  },
  {
    accessorKey: 'name',
    header: 'Product',
    cell: ({ row }) => {
      const product = row.original;
      return (
        <div className="flex flex-col space-y-1">
          <span className="font-medium truncate max-w-xs">{product.name || 'Unknown Product'}</span>
          <a
            href={product.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-muted-foreground hover:text-primary flex items-center space-x-1 w-fit"
            onClick={(e) => e.stopPropagation()}
          >
            <span>View on Myntra</span>
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      );
    },
  },
  {
    accessorKey: 'threshold_price',
    header: 'Alert Price',
    cell: ({ row }) => {
      const price = row.getValue('threshold_price') as number;
      return <span className="font-medium">₹{price?.toLocaleString() || 'N/A'}</span>;
    },
  },
  {
    accessorKey: 'current_price',
    header: 'Current Price',
    cell: ({ row }) => {
      const price = row.original.current_price;
      return price ? (
        <span className="font-medium">₹{price.toLocaleString()}</span>
      ) : (
        <span className="text-muted-foreground">Pending</span>
      );
    },
  },
  {
    accessorKey: 'last_scrape_status',
    header: 'Last Scrape', // Renamed for clarity
    cell: ({ row }) => {
      const status = row.getValue('last_scrape_status') as Product['last_scrape_status'];
      const variants: { [key: string]: 'default' | 'destructive' | 'secondary' } = {
        success: 'default',
        failed: 'destructive',
        pending: 'secondary',
      };
      return (
        <Badge variant={variants[status] || 'secondary'} className="capitalize">
          {status || 'unknown'}
        </Badge>
      );
    },
  },
  {
    accessorKey: 'active',
    header: 'Tracking', // The new column for the active/paused toggle
    cell: ({ row }) => {
      const product = row.original;
      return (
        <div className="flex items-center space-x-2">
          <Switch
            id={`active-switch-${product.product_id}`}
            checked={product.active}
            onCheckedChange={(newStatus) => onToggleStatus(product.product_id, newStatus)}
            aria-label={`Toggle tracking for ${product.name}`}
          />
        </div>
      );
    },
  },
  {
    accessorKey: 'timestamp', // Correctly uses 'timestamp'
    header: 'Last Updated',
    cell: ({ row }) => {
      const timestamp = row.getValue('timestamp') as string;
      return (
        <span className="text-sm text-muted-foreground">
          {formatTimestamp(timestamp)}
        </span>
      );
    },
  },
  {
    id: 'actions',
    cell: ({ row }) => {
      const product = row.original;
      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onEdit(product)}>
              <Edit className="mr-2 h-4 w-4" />
              Edit
            </DropdownMenuItem>
            <DropdownMenuItem
              onClick={() => onDelete(product)}
              className="text-destructive focus:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      );
    },
  },
];
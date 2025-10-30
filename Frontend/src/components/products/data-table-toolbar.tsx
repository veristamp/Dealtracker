// src/components/products/data-table-toolbar.tsx

import { Table } from '@tanstack/react-table';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { X, Trash2, Tag } from 'lucide-react';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

interface DataTableToolbarProps<TData> {
  table: Table<TData>;
  onBulkDelete: (selectedRows: TData[]) => void;
}

const tags = [
  { value: 'myntra', label: 'Myntra', icon: Tag },
  { value: 'flipkart', label: 'Flipkart', icon: Tag },
];

export function DataTableToolbar<TData>({
  table,
  onBulkDelete,
}: DataTableToolbarProps<TData>) {
  const isFiltered = table.getState().columnFilters.length > 0;
  const selectedRows = table.getFilteredSelectedRowModel().rows;
  const tagColumn = table.getColumn('tag');

  // FIX: Cast the filter value to string[] or an empty array
  const selectedTagValue = (tagColumn?.getFilterValue() as string[] | undefined) || [];

  return (
    <div className="flex items-center justify-between">
      <div className="flex flex-1 items-center space-x-2">
        <Input
          placeholder="Filter products..."
          value={(table.getColumn('name')?.getFilterValue() as string) ?? ''}
          onChange={(event) =>
            table.getColumn('name')?.setFilterValue(event.target.value)
          }
          className="h-8 w-[150px] lg:w-[250px]"
        />
        {tagColumn && (
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" size="sm" className="h-8 border-dashed">
                <Tag className="mr-2 h-4 w-4" />
                Source
                {selectedTagValue.length > 0 && (
                  <>
                    <Separator orientation="vertical" className="mx-2 h-4" />
                    <Badge
                      variant="secondary"
                      className="rounded-sm px-1 font-normal"
                    >
                      {
                        tags.find(
                          (tag) => tag.value === selectedTagValue[0]
                        )?.label
                      }
                    </Badge>
                  </>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[200px] p-0" align="start">
              <Command>
                <CommandInput placeholder="Select source..." />
                <CommandList>
                  <CommandEmpty>No results found.</CommandEmpty>
                  <CommandGroup>
                    {tags.map((option) => {
                      const isSelected = selectedTagValue.includes(option.value);
                      return (
                        <CommandItem
                          key={option.value}
                          onSelect={() => {
                            if (isSelected) {
                              tagColumn.setFilterValue(undefined);
                            } else {
                              tagColumn.setFilterValue([option.value]);
                            }
                          }}
                        >
                          <div
                            className={cn(
                              "mr-2 flex h-4 w-4 items-center justify-center rounded-sm border border-primary",
                              isSelected
                                ? "bg-primary text-primary-foreground"
                                : "opacity-50 [&_svg]:invisible"
                            )}
                          >
                           <option.icon className="h-4 w-4" />
                          </div>
                          <span>{option.label}</span>
                        </CommandItem>
                      );
                    })}
                  </CommandGroup>
                  {selectedTagValue.length > 0 && (
                    <>
                      <CommandSeparator />
                      <CommandGroup>
                        <CommandItem
                          onSelect={() => tagColumn.setFilterValue(undefined)}
                          className="justify-center text-center"
                        >
                          Clear filter
                        </CommandItem>
                      </CommandGroup>
                    </>
                  )}
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>
        )}
        {isFiltered && (
          <Button
            variant="ghost"
            onClick={() => table.resetColumnFilters()}
            className="h-8 px-2 lg:px-3"
          >
            Reset
            <X className="ml-2 h-4 w-4" />
          </Button>
        )}
      </div>
      {selectedRows.length > 0 && (
        <Button
          variant="destructive"
          size="sm"
          onClick={() => onBulkDelete(selectedRows.map(row => row.original))}
          className="h-8"
        >
          <Trash2 className="mr-2 h-4 w-4" />
          Delete Selected ({selectedRows.length})
        </Button>
      )}
    </div>
  );
}
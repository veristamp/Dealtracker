import { useState, useEffect, useCallback } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Plus, RefreshCw } from 'lucide-react';
import { DataTable } from '@/components/products/data-table';
import { createColumns } from '@/components/products/columns';
import { useStore } from '@/store/useStore';
import { api, ApiError } from '@/api';
import { Product } from '@/lib/types';
import { toast } from 'sonner';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

const tierLimits: { [key: string]: number } = {
  bronze: 20,
  silver: 50,
  gold: 100,
};

export default function Products() {
  const { products, setProducts, user } = useStore();
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [isBulkDeleteDialogOpen, setIsBulkDeleteDialogOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [selectedProductIds, setSelectedProductIds] = useState<number[]>([]);
  const [newProduct, setNewProduct] = useState({ url: '', price_threshold: '' });

  const fetchProducts = useCallback(async () => {
    setIsLoading(true);
    try {
      const fetchedProducts = await api.getProducts();
      if (Array.isArray(fetchedProducts)) {
        setProducts(fetchedProducts);
      } else {
        toast.error("Could not load products due to invalid server response.");
        setProducts([]);
      }
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        toast.error('Session expired. Please log in again.');
        useStore.getState().setUser(null);
      } else {
        toast.error('Failed to fetch products. Check the server connection.');
      }
    } finally {
      setIsLoading(false);
    }
  }, [setProducts]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const handleToggleProductStatus = async (productId: number, active: boolean) => {
    const originalProducts = [...products];
    const updatedProducts = products.map(p =>
      p.product_id === productId ? { ...p, active } : p
    );
    setProducts(updatedProducts);

    try {
      const response = await api.updateProductStatus(productId, active);
      if (!response.success) {
        throw new Error(response.message || 'Failed to update status');
      }
      toast.success(`Product tracking ${active ? 'activated' : 'paused'}.`);
    } catch (error) {
      toast.error('Failed to update product status. Reverting change.');
      setProducts(originalProducts);
    }
  };

  const handleAddProduct = async () => {
    if (!newProduct.url || !newProduct.price_threshold) {
      toast.error('Please fill in all fields');
      return;
    }
    if (!newProduct.url.includes('myntra.com')) {
      toast.error('Please provide a valid Myntra URL');
      return;
    }
    try {
      const response = await api.addProduct(newProduct.url, parseFloat(newProduct.price_threshold));
      if (response.success) {
        toast.success('Product added successfully!');
        setIsAddDialogOpen(false);
        setNewProduct({ url: '', price_threshold: '' });
        await fetchProducts();
      } else {
        toast.error(response.message || 'Failed to add product');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred while adding the product';
      toast.error(errorMessage);
    }
  };

  const handleDeleteProduct = async () => {
    if (!selectedProduct) return;
    try {
      const response = await api.deleteProduct(selectedProduct.product_id);
      if (response.success) {
        toast.success('Product deleted successfully!');
        setIsDeleteDialogOpen(false);
        setSelectedProduct(null);
        await fetchProducts();
      } else {
        toast.error(response.message || 'Failed to delete product');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred while deleting the product';
      toast.error(errorMessage);
    }
  };

  const handleBulkDelete = async () => {
    if (selectedProductIds.length === 0) return;
    try {
      const response = await api.bulkDeleteProducts(selectedProductIds);
      if (response.success) {
        toast.success(`${selectedProductIds.length} products deleted successfully!`);
        setIsBulkDeleteDialogOpen(false);
        setSelectedProductIds([]);
        await fetchProducts();
      } else {
        toast.error(response.message || 'Failed to delete products');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'An error occurred while deleting products';
      toast.error(errorMessage);
    }
  };

  const openDeleteDialog = (product: Product) => {
    setSelectedProduct(product);
    setIsDeleteDialogOpen(true);
  };

  const handleDeleteSelected = (selectedProducts: Product[]) => {
    if (selectedProducts.length > 0) {
      setSelectedProductIds(selectedProducts.map(p => p.product_id));
      setIsBulkDeleteDialogOpen(true);
    }
  };

  const columns = createColumns({
    onDelete: openDeleteDialog,
    onEdit: () => { toast.info('Edit functionality coming soon!') },
    onToggleStatus: handleToggleProductStatus,
  });

  const productCount = products.length;
  const userTier = user?.tier || 'bronze';
  const productLimit = tierLimits[userTier] || 20;
  const isLimitReached = productCount >= productLimit;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Products"
        description="Manage your tracked products and price alerts"
      >
        <div className="flex items-center space-x-4">
          <Badge variant="outline" className="text-sm">
            Tracking: {productCount} / {productLimit}
          </Badge>
          <div className="flex space-x-2">
            <Button variant="outline" onClick={fetchProducts} disabled={isLoading}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh
            </Button>
            <Button onClick={() => setIsAddDialogOpen(true)} disabled={isLimitReached}>
              <Plus className="mr-2 h-4 w-4" />
              Add Product
            </Button>
          </div>
        </div>
      </PageHeader>

      {isLimitReached && !isLoading && (
         <Alert variant="destructive">
            <AlertTitle>URL Limit Reached</AlertTitle>
            <AlertDescription>
                You have reached the maximum number of products for the <strong>{userTier}</strong> tier. Please remove a product to add a new one.
            </AlertDescription>
        </Alert>
      )}

      {isLoading ? (
        <div className="space-y-2">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : products.length === 0 ? (
        <Alert>
          <AlertDescription>No products found. Add a product to start tracking.</AlertDescription>
        </Alert>
      ) : (
        <DataTable
          columns={columns}
          data={products}
          onBulkDelete={handleDeleteSelected}
        />
      )}

      <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add New Product</DialogTitle>
            <DialogDescription>
              Add a Myntra product URL to start tracking price drops. Price and URL cannot be edited later.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="url">Myntra Product URL</Label>
              <Input
                id="url"
                value={newProduct.url}
                onChange={(e) => setNewProduct(prev => ({ ...prev, url: e.target.value }))}
                placeholder="https://www.myntra.com/..."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="price">Alert Price (₹)</Label>
              <Input
                id="price"
                type="number"
                value={newProduct.price_threshold}
                onChange={(e) => setNewProduct(prev => ({ ...prev, price_threshold: e.target.value }))}
                placeholder="Enter target price"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddDialogOpen(false)}>Cancel</Button>
            <Button onClick={handleAddProduct}>Add Product</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Product?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{selectedProduct?.name || 'this product'}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDeleteProduct} className="bg-destructive hover:bg-destructive/90">Delete</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={isBulkDeleteDialogOpen} onOpenChange={setIsBulkDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Selected Products?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete {selectedProductIds.length} products? This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleBulkDelete} className="bg-destructive hover:bg-destructive/90">Delete All</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
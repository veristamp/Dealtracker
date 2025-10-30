// src/app/Analytics.tsx (Corrected)

import { useState, useEffect, useCallback } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useStore } from '@/store/useStore';
import { api } from '@/api';
import { PriceHistory } from '@/lib/types';
import { format, parseISO } from 'date-fns';

export default function Analytics() {
  const { products } = useStore();
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [priceHistory, setPriceHistory] = useState<PriceHistory[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // FIX: Wrap the data fetching function in useCallback to give it a stable identity
  const fetchPriceHistory = useCallback(async (productId: number) => {
    setIsLoading(true);
    try {
      const response = await api.getProductHistory(productId);
      if (response.success && response.data) {
        setPriceHistory(response.data);
      } else {
        setPriceHistory([]);
      }
    } catch (error) {
      console.error('Failed to fetch price history:', error);
      setPriceHistory([]);
    } finally {
      setIsLoading(false);
    }
  }, []); // This function has no dependencies from the component scope

  // FIX: This useEffect now depends on the stable fetchPriceHistory callback
  useEffect(() => {
    if (selectedProductId) {
      fetchPriceHistory(parseInt(selectedProductId));
    } else {
      setPriceHistory([]); // Clear history if no product is selected
    }
  }, [selectedProductId, fetchPriceHistory]);

  const chartData = priceHistory.map(entry => ({
    timestamp: format(parseISO(entry.timestamp), 'MMM dd'),
    price: entry.price,
  }));
  
  const selectedProduct = products.find(p => p.product_id.toString() === selectedProductId);

  return (
    <div className="space-y-6">
      <PageHeader 
        title="Analytics" 
        description="Price history and trends for your tracked products"
      />
      <Card>
        <CardHeader>
          <CardTitle>Price History Chart</CardTitle>
          <CardDescription>Select a product to view its price trends over time.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="w-full max-w-sm">
            <Select value={selectedProductId} onValueChange={setSelectedProductId}>
              <SelectTrigger><SelectValue placeholder="Select a product" /></SelectTrigger>
              <SelectContent>
                {products.map((product) => (
                  <SelectItem key={product.product_id} value={product.product_id.toString()}>
                    {product.name || 'Unknown Product'}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="h-96 w-full pr-6">
            {isLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : chartData.length > 1 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="timestamp" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `₹${value}`} />
                  <Tooltip formatter={(value: number) => [`₹${value.toLocaleString()}`, 'Price']} />
                  <Legend />
                  <Line type="monotone" dataKey="price" name="Price" stroke="hsl(var(--primary))" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  {selectedProduct && (
                    <Line type="monotone" dataKey={() => selectedProduct.threshold_price} name="Target Price" stroke="hsl(var(--destructive))" strokeWidth={2} strokeDasharray="5 5" dot={false} activeDot={false} />
                  )}
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <div className="text-center">
                  <p className="text-lg font-medium">
                    {selectedProductId ? 'Not enough data to draw a chart.' : 'Please select a product.'}
                  </p>
                  <p className="text-sm">Price data will appear here after the product has been scraped at least twice.</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
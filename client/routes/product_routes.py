import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from ..dependencies import (
    api_client, auth_manager, db_manager, 
    sync_manager, get_current_user, activity_logger
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/products",
    tags=["Products"],
    dependencies=[Depends(get_current_user)]
)

class BulkDeletePayload(BaseModel):
    product_ids: List[int] = Field(..., min_items=1)

class ProductCreate(BaseModel):
    url: str
    price_threshold: float

class ProductUpdate(BaseModel):
    active: Optional[bool] = None
    threshold_price: Optional[float] = None

def get_api_client_with_token() -> api_client:
    token = auth_manager.get_access_token()
    if not token:
        raise HTTPException(status_code=401, detail="Session expired. Please log in again.")
    api_client.access_token = token
    return api_client

@router.get("/", response_model=List[dict])
async def get_all_products():
    try:
        return db_manager.get_cached_products(active_only=False)
    except Exception as e:
        logger.error(f"Failed to get cached products: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve products.")

@router.post("/")
async def add_product(payload: ProductCreate):
    if "myntra.com" not in payload.url:
        raise HTTPException(status_code=400, detail="Please provide a valid Myntra URL.")
    if payload.price_threshold <= 0:
        raise HTTPException(status_code=400, detail="Alert price must be greater than zero.")

    try:
        client = get_api_client_with_token()
        response = client.add_product(payload.url, payload.price_threshold)
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        await sync_manager.sync_products()
        activity_logger.log("PRODUCT_ADDED", {"url": payload.url})
        return {"success": True, "message": "Product added successfully!"}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error adding product: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while adding the product.")

@router.post("/bulk-delete")
async def bulk_delete_products(payload: BulkDeletePayload):
    try:
        client = get_api_client_with_token()
        for product_id in payload.product_ids:
            client.delete_product(product_id)
            db_manager.delete_product(product_id)
            db_manager.delete_alerts_for_product(product_id)

        await sync_manager.sync_products()
        activity_logger.log("PRODUCT_REMOVED_BULK", {"count": len(payload.product_ids)})
        return {"success": True, "message": f"{len(payload.product_ids)} products deleted."}
    except Exception as e:
        logger.error(f"Error during bulk delete: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during bulk deletion.")

@router.delete("/{product_id}")
async def delete_product(product_id: int):
    try:
        client = get_api_client_with_token()
        response = client.delete_product(product_id)
        
        if not response.success and response.status_code != 404:
            raise HTTPException(status_code=400, detail=response.message)

        db_manager.delete_product(product_id)
        db_manager.delete_alerts_for_product(product_id)
        
        await sync_manager.sync_products()
        activity_logger.log("PRODUCT_REMOVED", {"product_id": product_id})
        return {"success": True, "message": "Product deleted successfully."}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.error(f"Error deleting product {product_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while deleting the product.")

@router.put("/{product_id}")
async def update_product_local(product_id: int, payload: ProductUpdate):
    details_to_update = payload.model_dump(exclude_unset=True)
    if not details_to_update:
        raise HTTPException(status_code=400, detail="No update data provided.")
    
    try:
        db_manager.update_product_details(product_id, details_to_update)
        if 'threshold_price' in details_to_update:
            activity_logger.log("THRESHOLD_UPDATED", {"product_id": product_id, "new_threshold": details_to_update['threshold_price']})
        return {"success": True, "message": "Product updated locally."}
    except Exception as e:
        logger.error(f"Error updating local product {product_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not update product locally.")

@router.post("/sync")
async def manual_sync():
    try:
        if await sync_manager.sync_products():
            return {"success": True, "message": "Sync completed successfully."}
        else:
            raise HTTPException(status_code=500, detail="Sync failed. Check server logs.")
    except Exception as e:
        logger.error(f"Error during manual sync: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred during sync.")

@router.get("/{product_id}/history", response_class=JSONResponse)
async def get_product_price_history(product_id: int):
    try:
        history_data = db_manager.get_price_history_for_product(product_id)
        return {"success": True, "data": history_data}
    except Exception as e:
        logger.error(f"Failed to get price history for product {product_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve price history.")

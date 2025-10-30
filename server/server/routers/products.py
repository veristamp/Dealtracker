# server/routers/products.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Annotated

from .. import crud, schemas, auth, models

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/products",
    tags=["Products"],
    dependencies=[Depends(auth.get_current_active_user)]
)

@router.post("/", response_model=schemas.TrackedProduct, status_code=status.HTTP_201_CREATED)
def create_product_for_user(
    product: schemas.TrackedProductCreate,
    current_user: Annotated[models.User, Depends(auth.get_current_active_user)],
    db: Session = Depends(auth.get_db)
):
    """Create a new tracked product for the current user."""
    try:
        new_product = crud.create_user_product(db=db, product=product, user_id=current_user.id)
        if not new_product:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create product"
            )
        logger.info(f"Product created successfully for user {current_user.username}: {product.url}")
        return new_product
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating product for user {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )

@router.get("/", response_model=List[schemas.TrackedProduct])
def read_products(
    current_user: Annotated[models.User, Depends(auth.get_current_active_user)],
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(auth.get_db)
):
    """Get all tracked products (admin function)."""
    if current_user.tier != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    try:
        products = crud.get_products(db, skip=skip, limit=limit)
        logger.info(f"Retrieved {len(products)} products for admin user {current_user.username}")
        return products
    except Exception as e:
        logger.error(f"Error retrieving all products: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve products"
        )

# CRITICAL: /me route MUST come before /{product_id} route
@router.get("/me", response_model=List[schemas.TrackedProduct])
def read_my_products(
    current_user: Annotated[models.User, Depends(auth.get_current_active_user)],
    db: Session = Depends(auth.get_db)
):
    """Get all tracked products for the current user."""
    try:
        products = crud.get_user_products(db, user_id=current_user.id)
        logger.info(f"Retrieved {len(products)} products for user {current_user.username}")
        return products
    except Exception as e:
        logger.error(f"Error retrieving products for user {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve your products"
        )

# This route MUST come after /me to avoid conflicts
@router.get("/{product_id}", response_model=schemas.TrackedProduct)
def get_product(
    product_id: int,
    current_user: Annotated[models.User, Depends(auth.get_current_active_user)],
    db: Session = Depends(auth.get_db)
):
    """Get a specific product by ID (only if owned by current user)."""
    try:
        product = db.query(models.TrackedProduct).filter(
            models.TrackedProduct.id == product_id,
            models.TrackedProduct.owner_id == current_user.id
        ).first()
        
        if not product:
            logger.warning(f"Product {product_id} not found or not owned by user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or you don't have permission to access it"
            )
        
        logger.info(f"Product {product_id} retrieved by user {current_user.username}")
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving product {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product"
        )

@router.delete("/{product_id}", response_model=schemas.TrackedProduct)
def delete_product(
    product_id: int,
    current_user: Annotated[models.User, Depends(auth.get_current_active_user)],
    db: Session = Depends(auth.get_db)
):
    """Delete a tracked product."""
    try:
        # Get the product first to verify ownership and existence
        product = db.query(models.TrackedProduct).filter(
            models.TrackedProduct.id == product_id,
            models.TrackedProduct.owner_id == current_user.id
        ).first()
        
        if not product:
            logger.warning(f"Product {product_id} not found or not owned by user {current_user.username}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or you don't have permission to delete it"
            )
        
        # Store product data before deletion for response
        product_data = {
            "id": product.id,
            "url": product.url,
            "price_threshold": product.price_threshold,
            "owner_id": product.owner_id
        }
        
        # Delete the product
        db.delete(product)
        db.commit()
        
        logger.info(f"Product {product_id} deleted successfully by user {current_user.username}")
        return product_data
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error deleting product {product_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred while deleting product"
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting product {product_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )

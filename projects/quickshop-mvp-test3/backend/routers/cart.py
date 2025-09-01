"""
Cart router for shopping cart management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.database import get_db
from database import models
from schemas import schemas
from utils.auth import get_current_active_user

router = APIRouter()

@router.get("/", response_model=schemas.Cart)
async def get_cart(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get user's cart with items"""
    try:
        cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
        
        if not cart:
            # Create cart if it doesn't exist
            cart = models.Cart(user_id=current_user.id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
        
        # Get cart items with product details
        cart_items = []
        total = 0.0
        
        # Query cart items from the association table
        cart_items_query = db.execute(
            "SELECT ci.product_id, ci.quantity FROM cart_items ci WHERE ci.cart_id = ?",
            (cart.id,)
        ).fetchall()
        
        for item in cart_items_query:
            product = db.query(models.Product).filter(
                models.Product.id == item.product_id,
                models.Product.is_active == True
            ).first()
            
            if product:
                cart_item = schemas.CartItem(
                    product=schemas.ProductSimple(
                        id=product.id,
                        name=product.name,
                        price=product.price,
                        category=product.category,
                        image_url=product.image_url
                    ),
                    quantity=item.quantity
                )
                cart_items.append(cart_item)
                total += product.price * item.quantity
        
        return schemas.Cart(
            id=cart.id,
            items=cart_items,
            total=round(total, 2)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch cart"
        )

@router.post("/items", response_model=schemas.MessageResponse)
async def add_to_cart(
    item: schemas.CartItemAdd,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add item to cart"""
    try:
        # Check if product exists and is active
        product = db.query(models.Product).filter(
            models.Product.id == item.product_id,
            models.Product.is_active == True
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Check stock
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock"
            )
        
        # Get or create cart
        cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
        if not cart:
            cart = models.Cart(user_id=current_user.id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
        
        # Check if item already in cart
        existing_item = db.execute(
            "SELECT quantity FROM cart_items WHERE cart_id = ? AND product_id = ?",
            (cart.id, item.product_id)
        ).fetchone()
        
        if existing_item:
            # Update quantity
            new_quantity = existing_item[0] + item.quantity
            if product.stock_quantity < new_quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient stock for requested quantity"
                )
            
            db.execute(
                "UPDATE cart_items SET quantity = ? WHERE cart_id = ? AND product_id = ?",
                (new_quantity, cart.id, item.product_id)
            )
        else:
            # Add new item
            db.execute(
                "INSERT INTO cart_items (cart_id, product_id, quantity) VALUES (?, ?, ?)",
                (cart.id, item.product_id, item.quantity)
            )
        
        db.commit()
        
        return {"message": "Item added to cart successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add item to cart"
        )

@router.put("/items/{product_id}", response_model=schemas.MessageResponse)
async def update_cart_item(
    product_id: int,
    quantity: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update cart item quantity"""
    try:
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantity must be greater than 0"
            )
        
        cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )
        
        # Check if product exists and has sufficient stock
        product = db.query(models.Product).filter(
            models.Product.id == product_id,
            models.Product.is_active == True
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        if product.stock_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient stock"
            )
        
        # Update cart item
        result = db.execute(
            "UPDATE cart_items SET quantity = ? WHERE cart_id = ? AND product_id = ?",
            (quantity, cart.id, product_id)
        )
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found in cart"
            )
        
        db.commit()
        
        return {"message": "Cart item updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update cart item"
        )

@router.delete("/items/{product_id}", response_model=schemas.MessageResponse)
async def remove_from_cart(
    product_id: int,
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove item from cart"""
    try:
        cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )
        
        # Remove item from cart
        result = db.execute(
            "DELETE FROM cart_items WHERE cart_id = ? AND product_id = ?",
            (cart.id, product_id)
        )
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Item not found in cart"
            )
        
        db.commit()
        
        return {"message": "Item removed from cart successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove item from cart"
        )

@router.delete("/clear", response_model=schemas.MessageResponse)
async def clear_cart(
    current_user: models.User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Clear all items from cart"""
    try:
        cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
        if not cart:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart not found"
            )
        
        # Remove all items from cart
        db.execute("DELETE FROM cart_items WHERE cart_id = ?", (cart.id,))
        db.commit()
        
        return {"message": "Cart cleared successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cart"
        )
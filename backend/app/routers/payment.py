from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import stripe
from config import get_settings

router = APIRouter(prefix="/api", tags=["payment"])

settings = get_settings()
stripe.api_key = settings.STRIPE_SECRET_KEY


class CheckoutSessionRequest(BaseModel):
    plan: str  # "plus" or other plans


@router.post("/create-checkout-session")
async def create_checkout_session(request: CheckoutSessionRequest):
    """
    Create a Stripe Checkout Session for the specified plan.
    """
    try:
        # Define plan pricing
        plan_prices = {
            "plus": {
                "price": 1900,  # $19.00 in cents
                "name": "NMove Plus",
                "description": "Full features for active tracking"
            }
        }

        if request.plan not in plan_prices:
            raise HTTPException(status_code=400, detail="Invalid plan selected")

        plan_info = plan_prices[request.plan]

        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price_data': {
                        'currency': 'usd',
                        'unit_amount': plan_info['price'],
                        'product_data': {
                            'name': plan_info['name'],
                            'description': plan_info['description'],
                        },
                        'recurring': {
                            'interval': 'month',
                        },
                    },
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=settings.FRONTEND_URL + '/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=settings.FRONTEND_URL + '/pricing',
        )

        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create checkout session: {str(e)}"
        )

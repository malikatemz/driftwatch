"""
Billing routes — Stripe integration.
"""
from fastapi import APIRouter, Request, HTTPException
from app.core.database import get_supabase
from app.core.config import settings
import stripe

router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/create-checkout-session")
async def create_checkout_session(org_id: str, plan: str):
    """
    Create a Stripe Checkout session for subscription.
    Plan: starter, pro, enterprise
    """
    price_map = {
        "starter": settings.STRIPE_PRICE_STARTER,
        "pro": settings.STRIPE_PRICE_PRO,
        "enterprise": settings.STRIPE_PRICE_ENTERPRISE,
    }

    price_id = price_map.get(plan)
    if not price_id:
        raise HTTPException(status_code=400, detail="Invalid plan")

    sb = get_supabase()

    checkout_session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        metadata={"org_id": org_id},
        success_url="https://sentinelapi.io/dashboard?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://sentinelapi.io/pricing",
    )

    return {"url": checkout_session.url}


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Stripe sends events here.
    Must be registered at Stripe Dashboard → Webhooks.
    """
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")

    sb = get_supabase()

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        org_id = session["metadata"]["org_id"]
        # Update org plan
        sb.table("orgs").update({
            "plan": "pro",  # TODO: determine from price_id
            "stripe_customer_id": session["customer"],
        }).eq("clerk_org_id", org_id).execute()

    elif event["type"] == "customer.subscription.deleted":
        customer = event["data"]["object"]["customer"]
        sb.table("orgs").update({"plan": "starter"}).eq(
            "stripe_customer_id", customer
        ).execute()

    return {"status": "received"}


@router.get("/subscription/{org_id}")
async def get_subscription(org_id: str):
    sb = get_supabase()
    result = sb.table("orgs").select("plan, stripe_customer_id").eq(
        "clerk_org_id", org_id
    ).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Org not found")
    return result.data[0]

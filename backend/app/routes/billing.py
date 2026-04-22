"""
Billing routes — Stripe Checkout, webhook handler, and subscription management.
"""
from fastapi import APIRouter, Request, HTTPException
from app.core.database import get_supabase
from app.core.config import settings
import stripe

router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY

# Price ID cache — in production, fetch from Stripe API or database
_PRICE_TO_PLAN = {
    settings.STRIPE_PRICE_STARTER: "starter",
    settings.STRIPE_PRICE_PRO: "pro",
    settings.STRIPE_PRICE_ENTERPRISE: "enterprise",
}


# ─── Checkout ─────────────────────────────────────────────────────────────────
@router.post("/create-checkout-session")
async def create_checkout_session(org_id: str, plan: str):
    """
    Create a Stripe Checkout session for subscription upgrade.
    plan: starter | pro | enterprise
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
    # Get org name for Stripe session description
    org_result = sb.table("organizations").select("name").eq("id", org_id).execute()
    org_name = org_result.data[0]["name"] if org_result.data else "Driftwatch"

    checkout_session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        metadata={"org_id": org_id},
        success_url="https://driftwatch.dev/dashboard?session_id={CHECKOUT_SESSION_ID}",
        cancel_url="https://driftwatch.dev/pricing",
        subscription_data={
            "metadata": {"org_id": org_id},
        },
        allow_promotion_codes=True,
    )

    return {"url": checkout_session.url}


# ─── Stripe webhook ────────────────────────────────────────────────────────────
@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Stripe sends subscription events here.
    IMPORTANT: This endpoint must be registered at:
    Stripe Dashboard → Developers → Webhooks → Add endpoint
    URL: https://your-api.driftwatch.dev/api/v2/billing/webhook

    Verified via stripe-signature header using STRIPE_WEBHOOK_SECRET.
    """
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    if not sig:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid Stripe signature")

    sb = get_supabase()

    # ── Checkout completed — subscription is now active ──────────────────────
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")
        org_id = session.get("metadata", {}).get("org_id")

        if not org_id:
            # Legacy session — try to resolve from metadata
            return {"status": "received"}

        # Determine plan from subscription
        if subscription_id:
            sub = stripe.Subscription.retrieve(subscription_id)
            price_id = sub.get("items", {}).get("data", [{}])[0].get("price", {}).get("id")
            plan = _PRICE_TO_PLAN.get(price_id, "pro")
        else:
            plan = "pro"  # fallback

        sb.table("organizations").update({
            "plan": plan,
            "stripe_customer_id": customer_id,
            "stripe_subscription_id": subscription_id,
        }).eq("id", org_id).execute()

    # ── Subscription updated (plan change, renewal) ─────────────────────────
    elif event["type"] == "customer.subscription.updated":
        sub = event["data"]["object"]
        customer_id = sub.get("customer")
        subscription_id = sub.get("id")
        status = sub.get("status")  # active, past_due, canceled, etc.

        plan = "starter"  # default
        price_id = sub.get("items", {}).get("data", [{}])[0].get("price", {}).get("id")
        if price_id in _PRICE_TO_PLAN:
            plan = _PRICE_TO_PLAN[price_id]

        update = {"plan": plan}
        if status == "past_due":
            update["plan"] = "starter"  # downgrade on non-payment

        sb.table("organizations").update(update).eq(
            "stripe_customer_id", customer_id
        ).execute()

    # ── Subscription canceled — downgrade to starter ─────────────────────────
    elif event["type"] == "customer.subscription.deleted":
        customer = event["data"]["object"]["customer"]
        sb.table("organizations").update({
            "plan": "starter",
        }).eq("stripe_customer_id", customer).execute()

    # ── Payment failed — flag org for attention ────────────────────────────────
    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        customer_id = invoice.get("customer")

        # Create an alert for the payment failure
        sb.table("alerts").insert({
            "org_id": "unknown",  # resolved via customer lookup below
            "severity": "high",
            "type": "billing",
            "title": "Stripe payment failed",
            "description": f"Payment failed for customer {customer_id}. Invoice: {invoice.get('id')}",
            "remediation": "Check Stripe dashboard for failed payment details. Contact customer.",
        }).execute()

        # Try to resolve org from customer
        org_result = sb.table("organizations").select("id").eq(
            "stripe_customer_id", customer_id
        ).execute()
        if org_result.data:
            sb.table("alerts").update({"org_id": org_result.data[0]["id"]}).eq(
                "stripe_customer_id", customer_id
            ).execute()

    return {"status": "received"}


# ─── Get subscription ─────────────────────────────────────────────────────────
@router.get("/subscription/{org_id}")
async def get_subscription(org_id: str):
    sb = get_supabase()
    result = sb.table("organizations").select(
        "plan, stripe_customer_id, stripe_subscription_id"
    ).eq("id", org_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Organization not found")

    org = result.data[0]

    # Fetch live status from Stripe if we have a subscription ID
    sub_status = None
    if org.get("stripe_subscription_id"):
        try:
            sub = stripe.Subscription.retrieve(org["stripe_subscription_id"])
            sub_status = {
                "status": sub.get("status"),
                "current_period_end": sub.get("current_period_end"),
                "cancel_at_period_end": sub.get("cancel_at_period_end"),
            }
        except Exception:
            sub_status = {"status": "unknown"}

    return {
        "plan": org.get("plan", "starter"),
        "stripe_customer_id": org.get("stripe_customer_id"),
        "subscription": sub_status,
    }


# ─── Cancel subscription ──────────────────────────────────────────────────────
@router.post("/subscription/{org_id}/cancel")
async def cancel_subscription(org_id: str):
    sb = get_supabase()
    result = sb.table("organizations").select("stripe_subscription_id").eq("id", org_id).execute()
    if not result.data or not result.data[0].get("stripe_subscription_id"):
        raise HTTPException(status_code=404, detail="No active subscription found")

    stripe.Subscription.delete(result.data[0]["stripe_subscription_id"])
    sb.table("organizations").update({"plan": "starter"}).eq("id", org_id).execute()

    return {"status": "canceled"}
# 🚀 Stripe Payment Integration Setup Guide

This guide will help you set up Stripe payments for your Sora Watermark Remover application.

## 📋 Prerequisites

1. Stripe account (create at https://stripe.com)
2. Your application deployed or running locally
3. Environment variables configured

## 🔧 Step 1: Create Stripe Products and Prices

### 1.1 Login to Stripe Dashboard
- Go to https://dashboard.stripe.com
- Navigate to **Products** in the left sidebar

### 1.2 Create Monthly Plan Product
1. Click **"Add product"**
2. **Product name**: "Sora Watermark Remover - Monthly"
3. **Description**: "Monthly subscription for unlimited video processing"
4. **Pricing model**: Recurring
5. **Price**: $12.00 USD
6. **Billing period**: Monthly
7. Click **"Save product"**
8. **Copy the Price ID** (starts with `price_`) - you'll need this for `STRIPE_MONTHLY_PRICE_ID`

### 1.3 Create Yearly Plan Product
1. Click **"Add product"**
2. **Product name**: "Sora Watermark Remover - Yearly"
3. **Description**: "Yearly subscription for unlimited video processing"
4. **Pricing model**: Recurring
5. **Price**: $70.00 USD
6. **Billing period**: Yearly
7. Click **"Save product"**
8. **Copy the Price ID** (starts with `price_`) - you'll need this for `STRIPE_YEARLY_PRICE_ID`

## 🔑 Step 2: Get Stripe API Keys

### 2.1 Get API Keys
1. In Stripe Dashboard, go to **Developers** > **API keys**
2. Copy your **Publishable key** (starts with `pk_`)
3. Copy your **Secret key** (starts with `sk_`)

### 2.2 Get Webhook Secret
1. Go to **Developers** > **Webhooks**
2. Click **"Add endpoint"**
3. **Endpoint URL**: `https://your-backend-domain.com/api/stripe/webhook`
4. **Events to send**: Select these events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Click **"Add endpoint"**
6. Click on the webhook endpoint you just created
7. Click **"Reveal"** next to "Signing secret"
8. Copy the **Signing secret** (starts with `whsec_`)

## ⚙️ Step 3: Configure Environment Variables

### 3.1 Update your environment file
Add these variables to your `config.env` or production environment:

```bash
# Stripe Configuration
STRIPE_PUBLISHABLE_KEY=pk_live_your_actual_key_here
STRIPE_SECRET_KEY=sk_live_your_actual_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_actual_webhook_secret_here
STRIPE_MONTHLY_PRICE_ID=price_your_monthly_price_id_here
STRIPE_YEARLY_PRICE_ID=price_your_yearly_price_id_here

# Frontend URL (for redirects)
FRONTEND_URL=https://your-frontend-domain.com
```

### 3.2 For Development
Use test keys (starts with `pk_test_` and `sk_test_`) and test price IDs.

### 3.3 For Production
Use live keys (starts with `pk_live_` and `sk_live_`) and live price IDs.

## 🧪 Step 4: Test the Integration

### 4.1 Test Cards (Development Only)
Use these test card numbers:
- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **Requires authentication**: `4000 0025 0000 3155`

Use any future expiry date and any 3-digit CVC.

### 4.2 Test Flow
1. Start your application
2. Register/login as a user
3. Go to pricing page
4. Click "Choose Monthly" or "Choose Yearly"
5. You should be redirected to Stripe Checkout
6. Use test card details
7. Complete payment
8. You should be redirected back to dashboard with success message

## 🔍 Step 5: Verify Integration

### 5.1 Check Database
Verify that user's `subscription_tier` and `stripe_customer_id` are updated.

### 5.2 Check Stripe Dashboard
- Go to **Customers** - you should see your test customer
- Go to **Subscriptions** - you should see the active subscription
- Go to **Events** - you should see webhook events being received

### 5.3 Test Webhook
1. Go to **Developers** > **Webhooks**
2. Click on your webhook endpoint
3. Check **"Recent deliveries"** - should show successful deliveries

## 🚨 Troubleshooting

### Common Issues:

1. **"Invalid price ID" error**
   - Verify your price IDs are correct
   - Make sure you're using the right environment (test vs live)

2. **Webhook not receiving events**
   - Check webhook URL is accessible
   - Verify webhook secret is correct
   - Check server logs for errors

3. **Redirect URLs not working**
   - Verify `FRONTEND_URL` environment variable
   - Check that your frontend is accessible

4. **Payment succeeds but subscription not updated**
   - Check webhook endpoint is working
   - Verify database connection
   - Check server logs for webhook processing errors

### Debug Steps:
1. Check server logs for errors
2. Test webhook endpoint manually
3. Verify all environment variables are set
4. Check Stripe Dashboard for failed events

## 📞 Support

If you encounter issues:
1. Check Stripe Dashboard for error details
2. Review server logs
3. Test with Stripe's webhook testing tool
4. Verify all environment variables are correctly set

## 🎉 Success!

Once everything is working:
- Users can subscribe to monthly/yearly plans
- Payments are processed securely through Stripe
- Subscriptions are automatically managed
- Users get redirected back to your app after payment
- Webhooks keep your database in sync with Stripe

Your payment integration is now complete! 🚀


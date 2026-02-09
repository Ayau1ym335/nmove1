# Installation Instructions

## 1. Install Stripe Python Library

You need to install the Stripe library for Python. Run this command in your backend directory:

```bash
pip install stripe
```

## 2. Configure Gmail App Password

To send emails via Gmail, you need to generate an **App Password**:

1. Go to your Google Account: https://myaccount.google.com/
2. Select **Security** from the left menu
3. Under "How you sign in to Google," select **2-Step Verification** (you must enable this first if not already enabled)
4. At the bottom, select **App passwords**
5. Select "Mail" and "Windows Computer" (or "Other")
6. Click **Generate**
7. Copy the 16-character password (without spaces)
8. Add it to your `.env` file:
   ```
   MAIL_PASSWORD=your_16_char_password_here
   ```

## 3. Configure Stripe API Key

To accept payments, you need a Stripe account and API key:

1. Sign up or log in to Stripe: https://dashboard.stripe.com/
2. Switch to **Test Mode** (toggle in the top right)
3. Go to **Developers** > **API keys**
4. Copy the **Secret key** (starts with `sk_test_`)
5. Add it to your `.env` file:
   ```
   STRIPE_SECRET_KEY=sk_test_your_secret_key_here
   ```

## 4. Restart the Backend Server

After updating the `.env` file, restart your backend server for the changes to take effect.

## Testing

### Email Contact Form
1. Go to http://localhost:5173/contact
2. Fill out the form and submit
3. Check your inbox at nmove.co@gmail.com

### Stripe Payment
1. Go to http://localhost:5173/pricing
2. Click "Subscribe" on the Plus plan
3. You'll be redirected to Stripe Checkout (Test Mode)
4. Use test card: `4242 4242 4242 4242`, any future expiry date, any CVC

## Important Notes

- The backend must be running on `http://localhost:8000`
- The frontend must be running on `http://localhost:5173`
- Both MAIL_PASSWORD and STRIPE_SECRET_KEY must be set in `.env` for the features to work

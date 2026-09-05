# Renewing the Gmail API Refresh Token

The refresh token used for sending newsletters expires roughly every 7 days (since the Google app isn't fully verified). When sending stops working, follow these steps to generate a new one — takes about 5 minutes.

## Steps

1. Make sure you're logged into your browser as **cyai.club@gmail.com** (not a personal account).
2. Go to **https://developers.google.com/oauthplayground**
3. Click the **gear icon** (top right) → check **"Use your own OAuth credentials"**
4. Enter the **Client ID** and **Client Secret** (saved securely by the club - ask the outgoing officer, or find them in Google Cloud Console under the "CYAI Club Assistant" project → APIs & Services → Credentials)
5. Close settings. On the left side, find **Gmail API v1** in the list, expand it, and check the box for:
6. Click **"Authorize APIs"**
7. Log in as cyai.club@gmail.com, click through the "unverified app" warning (Advanced → Go to CYAI Backend, unsafe) — this is expected and safe.
8. Back on the Playground, click **"Exchange authorization code for tokens"**
9. Copy the **refresh_token** value from the response.

## Updating the App

1. Go to **Render.com** → your backend service → **Environment** tab
2. Update the `GMAIL_REFRESH_TOKEN` value with the new token
3. Save — Render will automatically redeploy

That's it. Sending should work again immediately after the redeploy finishes.

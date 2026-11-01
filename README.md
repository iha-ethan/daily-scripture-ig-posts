# Daily Scripture IG Posts

Every morning, a GitHub Action:

1. Picks the day's verse from [`verses.txt`](verses.txt) (line N = day N of the year, Genesis 1:1 on Jan 1 through Revelation on Dec 31).
2. Fetches the NLT text from Tyndale's official [NLT API](https://api.nlt.to).
3. Grabs a nature photo from Unsplash, darkens and softens it, and sets the verse on top (1080×1350, Instagram's 4:5 portrait size).
4. Posts it to Instagram with a caption that includes the verse, hashtags, the NLT copyright notice and the photo credit.

Each rendered image is saved in `posts/`, and a post is never published twice for the same day.

## One-time setup

### 1. Put this folder on GitHub
- Create a **public** repository at https://github.com/new. It has to be public because Instagram downloads the image from GitHub. No secrets are stored in the code.
- Upload the contents of this folder, including the hidden `.github` folder. Either drag the files into the GitHub web page, or use GitHub Desktop.

### 2. Get free API keys
| Secret name | Where to get it |
|---|---|
| `NLT_API_KEY` | Sign up at https://api.nlt.to. Without a key it falls back to a rate-limited demo key. |
| `UNSPLASH_ACCESS_KEY` | https://unsplash.com/developers → **New Application** → copy the **Access Key**. Without a key it uses generated gradient backgrounds. |

### 3. Connect Instagram
1. In the Instagram app, switch your account to a **Professional** account (Settings → Account type and tools). Either Creator or Business works, and it's free.
2. Go to https://developers.facebook.com/apps → **Create app** → choose the use case **"Manage messaging & content on Instagram"**.
3. In the app, open **Instagram → API setup with Instagram login**.
   - Under **Generate access tokens**, click **Add account** and log in to your Instagram account.
   - Make sure the permissions `instagram_business_basic` and `instagram_business_content_publish` are included.
   - Copy the **access token** and the **Instagram user ID** shown next to your account.

   While the app is in Development mode, it can post to your own account. You don't need app review for that.

Save these as secrets:

| Secret name | Value |
|---|---|
| `IG_USER_ID` | the numeric Instagram user ID |
| `IG_ACCESS_TOKEN` | the access token |

### 4. Keep the token alive (recommended)
Instagram tokens expire after 60 days. The **Refresh Instagram token** workflow renews it on the 1st of each month, but it needs permission to update the secret:
- Create a token at https://github.com/settings/personal-access-tokens/new: **Only select repositories** → this repo → **Repository permissions → Secrets: Read and write**.
- Save it as the secret `GH_PAT`.

### 5. Add the secrets
In your repo: **Settings → Secrets and variables → Actions → New repository secret**, and add each one above.

Optional settings go under **Variables** on the same page:

| Variable | Example | Default |
|---|---|---|
| `TIMEZONE` | `America/Chicago` | `America/New_York` |
| `IG_HANDLE` | `@yourhandle`, printed small at the bottom of the image | none |
| `HASHTAGS` | `#dailyverse #faith` | a built-in set |

### 6. Test it
- **Actions → Daily scripture post → Run workflow**, with **dry run** left checked.
- When it finishes, download the image from the run's **Artifacts** to preview it. Nothing is posted.
- To do a real post right away, run it again with **dry run** unchecked.

After that, it posts automatically every day at 12:00 UTC (8 AM Eastern). To change the time, edit the `cron` line in [`.github/workflows/daily-post.yml`](.github/workflows/daily-post.yml).

## Customizing
- **Verses:** edit `verses.txt`, one reference per line, like `Philippians 4:6-7`.
- **Photo themes:** edit `SEARCH_TERMS` in [`background.py`](background.py).
- **Look:** fonts, colors, darkness and layout are in [`render.py`](render.py). The fonts are Lora and Montserrat (SIL Open Font License, see `fonts/`).

## About NLT permissions
Tyndale lets you quote up to 500 NLT verses without written permission, as long as the copyright notice is included. That notice is added to every caption automatically. A year of daily posts is about 400–450 verses, because some days use 2–3 verses. If you plan to run this for more than a year, or use it commercially, ask Tyndale for permission: https://www.tyndale.com/permissions

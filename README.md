# Remote Job Hunt AI — Streamlit

### Deploy
Upload `app.py`, `profile.json`, and `requirements.txt` to GitHub, then deploy `app.py` on Streamlit Community Cloud.

In Streamlit **Secrets** add:
```toml
SERPAPI_KEY = "YOUR_KEY"
```

The app automatically searches multiple role families, deduplicates jobs, excludes already-applied companies, scores India-remote/full-time/entry-level fit, rejects customer-support/freelance/scam signals, and provides direct application links plus export.

### Important
Streamlit can automate the hunt when the app is run, but it is not a reliable 24/7 scheduler. A separate GitHub Actions/cron layer is needed for unattended daily execution.

It deliberately does not submit applications, bypass CAPTCHA/OTP, use passwords, impersonate you, or fabricate qualifications.

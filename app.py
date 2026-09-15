import streamlit as st
import requests, re, json, csv, io
from datetime import datetime
from urllib.parse import urlparse

st.set_page_config(page_title="Remote Job Hunt AI", page_icon="🎯", layout="wide")

DEFAULT_PROFILE = {
    "name": "Aryan Mishra",
    "country": "India",
    "skills": ["Excel","Google Sheets","SQL","Python","Data Analysis","Data Quality","AI Evaluation","QA Testing","Research","Data Operations","Reporting","n8n","Workflow Automation"],
    "preferred_roles": ["Data Analyst","Data Quality Analyst","Data Operations","AI Data Operations","AI Evaluation","Manual QA Tester","Research Analyst","Reporting Analyst","Junior Business Analyst","Operations Analyst","Data Processing"],
    "exclude_roles": ["Customer Support","Call Center","Telecaller","Sales","Commission","Field Sales","Door to Door","Freelance","Gig","Driver","Delivery"],
    "already_applied": ["Mindrift","DataAnnotation","Alignerr","OneForma","Outlier","TELUS Digital AI Community","Appen","OpenTrain","Remotasks","Clickworker","Microworkers","Fiverr","Freelancer","PeoplePerHour","SproutGigs"]
}

def profile():
    try:
        with open("profile.json","r",encoding="utf-8") as f: return {**DEFAULT_PROFILE, **json.load(f)}
    except: return DEFAULT_PROFILE

def search(api_key, q, location):
    p={"engine":"google_jobs","q":q,"location":location,"hl":"en","api_key":api_key}
    return requests.get("https://serpapi.com/search.json",params=p,timeout=30).json().get("jobs_results",[])

def clean(x): return re.sub(r"\s+"," ",str(x or "")).strip()

def score(j,p):
    title=clean(j.get("title")); company=clean(j.get("company_name")); loc=clean(j.get("location")); desc=clean(j.get("description"))
    t=f"{title} {company} {loc} {desc}".lower()
    s=0; good=[]; bad=[]
    if "remote" in t: s+=25; good.append("Remote")
    if any(x in t for x in ["india","new delhi","delhi","mumbai","bengaluru","bangalore","hyderabad","pune","noida","gurugram","work from india"]): s+=20; good.append("India signal")
    else: bad.append("India eligibility unclear")
    if any(x in t for x in ["full-time","full time","permanent","employee"]): s+=15; good.append("Full-time/employee")
    if any(x in t for x in ["contract","contractor","temporary"]): s-=12; bad.append("Contract signal")
    if any(x in t for x in ["freelance","gig","independent contractor"]): s-=35; bad.append("Freelance/gig")
    rh=[x for x in p["preferred_roles"] if x.lower() in t]; sh=[x for x in p["skills"] if x.lower() in t]
    s+=min(25,len(rh)*8)+min(20,len(sh)*3)
    if rh: good.append("Role: "+", ".join(rh[:3]))
    if sh: good.append("Skills: "+", ".join(sh[:6]))
    if any(x in t for x in ["entry level","entry-level","0-1 years","0–1 years","0-2 years","no experience","graduate"]): s+=12; good.append("Entry-level")
    if any(x in t for x in ["2+ years","3+ years","3 years","4 years","5 years"]): s-=8; bad.append("Higher experience may be required")
    ex=[x for x in p["exclude_roles"] if x.lower() in t]
    if ex: s-=60; bad.append("Excluded: "+", ".join(ex[:3]))
    scam=["registration fee","application fee","security deposit","pay to apply","paid training required","telegram payment","whatsapp only","guaranteed income"]
    sc=[x for x in scam if x in t]
    if sc: s-=100; bad.append("Scam signal: "+", ".join(sc))
    links=[a.get("link") for a in (j.get("apply_options") or []) if isinstance(a,dict) and a.get("link")]
    if links: s+=5
    status="APPLY NOW" if s>=65 else "STRETCH" if s>=45 else "REJECT"
    return s,status,good,bad,links

p=profile()
st.title("🎯 Remote Job Hunt AI Agent")
st.caption("Live search → strict filtering → scoring → shortlist → direct application links → export")

with st.sidebar:
    key=st.text_input("SerpAPI key",value=st.secrets.get("SERPAPI_KEY",""),type="password")
    location=st.text_input("Search location","India")
    limit=st.slider("Jobs to keep",10,100,40)
    modes=st.multiselect("Search modes",["Data/Analytics","AI/Data","QA/Testing","Research/Operations"],["Data/Analytics","AI/Data","QA/Testing","Research/Operations"])

tabs=st.tabs(["🔎 Full Hunt","🧠 Profile","📌 Tracker","📤 Export"])

with tabs[0]:
    qs=[]
    if "Data/Analytics" in modes: qs += ["remote entry level data analyst India","remote junior data analyst India","remote data quality analyst India"]
    if "AI/Data" in modes: qs += ["remote AI data operations India","remote AI evaluator India","remote data operations India"]
    if "QA/Testing" in modes: qs += ["remote junior QA tester India","remote manual QA analyst India"]
    if "Research/Operations" in modes: qs += ["remote research analyst India entry level","remote operations analyst India entry level"]

    if st.button("🚀 RUN FULL JOB HUNT",type="primary",use_container_width=True):
        if not key: st.error("Add SERPAPI_KEY in the sidebar or Streamlit Secrets.")
        else:
            jobs=[]; bar=st.progress(0)
            for i,q in enumerate(qs):
                try: jobs += search(key,q,location)
                except Exception as e: st.warning(f"Search failed: {q} — {e}")
                bar.progress((i+1)/len(qs))
            seen=set(); out=[]
            for j in jobs:
                k=(clean(j.get("title")).lower(),clean(j.get("company_name")).lower(),clean(j.get("location")).lower())
                if k in seen: continue
                seen.add(k)
                if any(a.lower() in clean(j.get("company_name")).lower() for a in p["already_applied"]): continue
                out.append((score(j,p),j))
            out.sort(key=lambda x:x[0][0],reverse=True)
            st.session_state.jobs=out[:limit]
            st.success(f"Finished. {len(st.session_state.jobs)} unique jobs shortlisted.")

    jobs=st.session_state.get("jobs",[])
    if jobs:
        a=sum(x[0][1]=="APPLY NOW" for x in jobs)
        b=sum(x[0][1]=="STRETCH" for x in jobs)
        c1,c2,c3=st.columns(3); c1.metric("Jobs",len(jobs)); c2.metric("Apply Now",a); c3.metric("Stretch",b)
        for (sc,j), in [(x,) for x in jobs]:
            s,status,good,bad,links=sc
            with st.container(border=True):
                c1,c2=st.columns([5,1])
                with c1:
                    st.markdown(f"### {clean(j.get('title'))}")
                    st.write(f"**{clean(j.get('company_name'))}** • {clean(j.get('location'))}")
                with c2:
                    st.metric("Score",s); st.write(status)
                if good: st.write("✅ "+" • ".join(good[:5]))
                if bad: st.warning("⚠️ "+" • ".join(bad[:4]))
                d=clean(j.get("description"))
                if d: st.write(d[:650]+("…" if len(d)>650 else ""))
                if links: st.link_button("Apply / Review",links[0],use_container_width=True)
                else: st.info("No direct application URL returned.")

with tabs[1]:
    st.subheader("Save your profile once")
    name=st.text_input("Name",p["name"])
    skills=st.text_area("Skills (one per line)","\n".join(p["skills"]))
    roles=st.text_area("Preferred roles (one per line)","\n".join(p["preferred_roles"]))
    excludes=st.text_area("Reject keywords (one per line)","\n".join(p["exclude_roles"]))
    applied=st.text_area("Already applied companies/platforms (one per line)","\n".join(p["already_applied"]))
    if st.button("💾 Save Profile"):
        new={**p,"name":name,"skills":[x.strip() for x in skills.splitlines() if x.strip()],"preferred_roles":[x.strip() for x in roles.splitlines() if x.strip()],"exclude_roles":[x.strip() for x in excludes.splitlines() if x.strip()],"already_applied":[x.strip() for x in applied.splitlines() if x.strip()]}
        with open("profile.json","w",encoding="utf-8") as f: json.dump(new,f,indent=2,ensure_ascii=False)
        st.success("Saved.")

with tabs[2]:
    st.subheader("Application tracker")
    if "tracker" not in st.session_state: st.session_state.tracker=[]
    company=st.text_input("Company"); role=st.text_input("Role"); status=st.selectbox("Status",["Saved","Applied","Assessment","Interview","Rejected","Offer"])
    if st.button("➕ Add"): st.session_state.tracker.append({"company":company,"role":role,"status":status,"date":datetime.now().strftime("%Y-%m-%d")})
    if st.session_state.tracker: st.dataframe(st.session_state.tracker,use_container_width=True)

with tabs[3]:
    rows=[]
    for (sc,j) in st.session_state.get("jobs",[]):
        s,status,good,bad,links=sc
        rows.append({"score":s,"status":status,"company":clean(j.get("company_name")),"role":clean(j.get("title")),"location":clean(j.get("location")),"apply_url":links[0] if links else "","reasons":" | ".join(good),"risks":" | ".join(bad)})
    if rows:
        b=io.StringIO(); w=csv.DictWriter(b,fieldnames=rows[0]); w.writeheader(); w.writerows(rows)
        st.download_button("⬇️ CSV",b.getvalue(),"remote_jobs.csv","text/csv")
        st.download_button("⬇️ JSON",json.dumps(rows,indent=2),"remote_jobs.json","application/json")
    else: st.info("Run the hunt first.")

st.divider()
st.caption("Human-in-the-loop by design: no fake applications, password/OTP entry, CAPTCHA bypass, or fabricated qualifications.")

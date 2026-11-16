import os,re
from datetime import date
from dotenv import load_dotenv
from fastapi import FastAPI,Request,Depends,Form,HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import select,func
from starlette.middleware.sessions import SessionMiddleware
from .db import Base,engine,get_db,SessionLocal
from .models import Clinic,User,Token
from .security import make_hash,check
load_dotenv()
secret=os.getenv("SECRET_KEY","")
if len(secret)<24: raise RuntimeError("Set a SECRET_KEY of at least 24 characters in .env")
app=FastAPI(title="QueueLess")
app.add_middleware(SessionMiddleware,secret_key=secret,same_site="lax",https_only=os.getenv("COOKIE_HTTPS_ONLY","false")=="true")
app.mount("/static",StaticFiles(directory="app/static"),name="static")
templates=Jinja2Templates(directory="app/templates")
def render(req,name,**kw): return templates.TemplateResponse(name,{"request":req,**kw})
def user_for(req,db): 
    uid=req.session.get("uid")
    return db.get(User,int(uid)) if uid else None
def slugify(s): return re.sub(r"[^a-z0-9]+","-",s.lower()).strip("-")[:70] or "clinic"
@app.on_event("startup")
def startup():
    Base.metadata.create_all(engine)
    name=os.getenv("SEED_CLINIC_NAME","").strip(); slug=os.getenv("SEED_CLINIC_SLUG","").strip()
    email=os.getenv("SEED_ADMIN_EMAIL","").strip().lower(); pw=os.getenv("SEED_ADMIN_PASSWORD","")
    if name and slug and email and pw:
        with SessionLocal() as db:
            clinic=db.scalar(select(Clinic).where(Clinic.slug==slug))
            if not clinic:
                clinic=Clinic(name=name,slug=slug,city="Nawabshah"); db.add(clinic); db.flush()
            if not db.scalar(select(User).where(User.email==email)):
                db.add(User(clinic_id=clinic.id,name=os.getenv("SEED_ADMIN_NAME","Admin"),email=email,password_hash=make_hash(pw)))
            db.commit()
@app.get("/")
def home(req:Request,db:Session=Depends(get_db)):
    clinics=db.scalars(select(Clinic).where(Clinic.active==True).order_by(Clinic.name)).all()
    return render(req,"home.html",clinics=clinics)
@app.get("/register")
def regpage(req:Request): return render(req,"register.html",error=None)
@app.post("/register")
def register(req:Request,clinic_name:str=Form(...),city:str=Form(""),phone:str=Form(""),owner:str=Form(...),email:str=Form(...),password:str=Form(...),db:Session=Depends(get_db)):
    email=email.strip().lower()
    if len(password)<10: return render(req,"register.html",error="Password must be at least 10 characters.")
    if db.scalar(select(User).where(User.email==email)): return render(req,"register.html",error="Email already registered.")
    base=slugify(clinic_name); slug=base; n=2
    while db.scalar(select(Clinic).where(Clinic.slug==slug)): slug=f"{base}-{n}"; n+=1
    c=Clinic(name=clinic_name.strip(),slug=slug,city=city.strip(),phone=phone.strip()); db.add(c); db.flush()
    u=User(clinic_id=c.id,name=owner.strip(),email=email,password_hash=make_hash(password)); db.add(u); db.commit()
    req.session["uid"]=u.id
    return RedirectResponse("/dashboard",303)
@app.get("/login")
def loginpage(req:Request): return render(req,"login.html",error=None)
@app.post("/login")
def login(req:Request,email:str=Form(...),password:str=Form(...),db:Session=Depends(get_db)):
    u=db.scalar(select(User).where(User.email==email.strip().lower()))
    if not u or not check(password,u.password_hash): return render(req,"login.html",error="Incorrect email or password.")
    req.session.clear(); req.session["uid"]=u.id
    return RedirectResponse("/dashboard",303)
@app.post("/logout")
def logout(req:Request):
    req.session.clear(); return RedirectResponse("/",303)
@app.get("/dashboard")
def dashboard(req:Request,db:Session=Depends(get_db)):
    u=user_for(req,db)
    if not u: return RedirectResponse("/login",303)
    c=db.get(Clinic,u.clinic_id)
    tokens=db.scalars(select(Token).where(Token.clinic_id==c.id,func.date(Token.created)==date.today()).order_by(Token.number)).all()
    return render(req,"dashboard.html",user=u,clinic=c,tokens=tokens,
        waiting=sum(t.status=="Waiting" for t in tokens),serving=sum(t.status=="Serving" for t in tokens),
        completed=sum(t.status=="Completed" for t in tokens))
@app.get("/clinic/{slug}")
def clinicpage(req:Request,slug:str,db:Session=Depends(get_db)):
    c=db.scalar(select(Clinic).where(Clinic.slug==slug,Clinic.active==True))
    if not c: raise HTTPException(404,"Clinic not found")
    current=db.scalar(select(Token).where(Token.clinic_id==c.id,func.date(Token.created)==date.today(),Token.status=="Serving").order_by(Token.number).limit(1))
    return render(req,"clinic.html",clinic=c,current=current)
@app.post("/clinic/{slug}/token")
def newtoken(slug:str,patient:str=Form(...),phone:str=Form(""),db:Session=Depends(get_db)):
    c=db.scalar(select(Clinic).where(Clinic.slug==slug,Clinic.active==True))
    if not c: raise HTTPException(404,"Clinic not found")
    if not patient.strip(): raise HTTPException(400,"Patient name required")
    last=db.scalar(select(func.max(Token.number)).where(Token.clinic_id==c.id,func.date(Token.created)==date.today())) or 0
    t=Token(clinic_id=c.id,number=last+1,patient=patient.strip()[:120],phone=phone.strip()[:40]); db.add(t); db.commit()
    return RedirectResponse(f"/token/{t.id}",303)
@app.get("/token/{tid}")
def tokenpage(req:Request,tid:int,db:Session=Depends(get_db)):
    t=db.get(Token,tid)
    if not t: raise HTTPException(404,"Token not found")
    c=db.get(Clinic,t.clinic_id)
    ahead=db.scalar(select(func.count()).select_from(Token).where(Token.clinic_id==c.id,func.date(Token.created)==date.today(),Token.number<t.number,Token.status=="Waiting")) or 0
    return render(req,"token.html",token=t,clinic=c,ahead=ahead)
def authorized(req,db,tid):
    u=user_for(req,db)
    if not u: return None,None
    t=db.get(Token,tid)
    if not t or t.clinic_id!=u.clinic_id: raise HTTPException(404,"Token not found")
    return u,t
@app.post("/queue/next")
def next_patient(req:Request,db:Session=Depends(get_db)):
    u=user_for(req,db)
    if not u: return RedirectResponse("/login",303)
    active=db.scalars(select(Token).where(Token.clinic_id==u.clinic_id,func.date(Token.created)==date.today(),Token.status=="Serving")).all()
    for t in active: t.status="Completed"
    t=db.scalar(select(Token).where(Token.clinic_id==u.clinic_id,func.date(Token.created)==date.today(),Token.status=="Waiting").order_by(Token.number).limit(1))
    if t: t.status="Serving"
    db.commit(); return RedirectResponse("/dashboard",303)
@app.post("/queue/{tid}/call")
def callone(tid:int,req:Request,db:Session=Depends(get_db)):
    u,t=authorized(req,db,tid)
    if not u: return RedirectResponse("/login",303)
    for old in db.scalars(select(Token).where(Token.clinic_id==u.clinic_id,func.date(Token.created)==date.today(),Token.status=="Serving")).all(): old.status="Completed"
    t.status="Serving"; db.commit(); return RedirectResponse("/dashboard",303)
@app.post("/queue/{tid}/status")
def status(tid:int,req:Request,status:str=Form(...),db:Session=Depends(get_db)):
    u,t=authorized(req,db,tid)
    if not u: return RedirectResponse("/login",303)
    if status not in ["Waiting","Completed","Skipped"]: raise HTTPException(400,"Invalid status")
    t.status=status; db.commit(); return RedirectResponse("/dashboard",303)
@app.get("/health")
def health(): return {"status":"ok"}

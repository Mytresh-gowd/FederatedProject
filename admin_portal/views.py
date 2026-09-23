from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render,redirect
from django.contrib import messages
from django.utils import timezone
from patient.models import Prediction
from hospital.models import Submission,FederatedRound
from services.ml_service import model_info
from services.fl_service import aggregate,UPLOAD_DIR
from pathlib import Path

def staff(u): return u.is_authenticated and (u.is_staff or getattr(getattr(u,'profile',None),'role',None)=='ADMIN')

def guard(view):
    return user_passes_test(staff,login_url='/login/')(view)

@guard
def dashboard(request):
    rounds=FederatedRound.objects.all()[:8]
    return render(request,'admin_portal/dashboard.html',{'users':User.objects.count(),'patients':Prediction.objects.values('patient').distinct().count(),'predictions':Prediction.objects.count(),'submissions':Submission.objects.count(),'rounds':rounds,'model':model_info()})

@guard
def hospitals(request): return render(request,'admin_portal/hospitals.html',{'items':Submission.objects.select_related('hospital').all()})

@guard
def patients(request): return render(request,'admin_portal/patients.html',{'items':Prediction.objects.select_related('patient').all()})

@guard
def rounds(request): return render(request,'admin_portal/rounds.html',{'items':FederatedRound.objects.all()})

@guard
def aggregate_round(request, round_no):
    rnd=FederatedRound.objects.get(round_no=round_no)
    subs=list(Submission.objects.filter(round_no=round_no,status='SUBMITTED').select_related('hospital__profile'))
    if len(subs)<3:
        messages.error(request,f'Need 3 submitted hospital updates; currently {len(subs)}.')
        return redirect('admin_rounds')
    bundle=[]
    for s in subs:
        cid=s.hospital.profile.client_id
        bundle.append({'path':str(UPLOAD_DIR/f'{cid}_round_{round_no}.joblib')})
    try:
        out,trees=aggregate(round_no,bundle)
        s_ids=[s.id for s in subs]
        Submission.objects.filter(id__in=s_ids).update(status='AGGREGATED')
        rnd.clients=len(subs); rnd.global_trees=trees; rnd.status='COMPLETED'; rnd.completed_at=timezone.now(); rnd.global_model_version=f'v{round_no+1}.0.0'; rnd.save()
        messages.success(request,f'Round {round_no} aggregated into {trees} trees. Artifact: {Path(out).name}')
    except Exception as exc: messages.error(request,str(exc))
    return redirect('admin_rounds')

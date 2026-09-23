from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect
from django.contrib import messages
from .models import Submission,FederatedRound
from services.fl_service import train_local_model, aggregate, LOCAL_TREES
from services.ml_service import model_info

def hospital_only(view):
    def wrapped(request,*args,**kwargs):
        p=getattr(request.user,'profile',None)
        if not request.user.is_authenticated or not p or p.role!='HOSPITAL': return redirect('login')
        return view(request,*args,**kwargs)
    return wrapped

@login_required
def dashboard(request):
    p=getattr(request.user,'profile',None)
    if not p or p.role!='HOSPITAL': return redirect('dashboard')
    items=Submission.objects.filter(hospital=request.user)
    rounds=FederatedRound.objects.all()[:6]
    return render(request,'hospital/dashboard.html',{'items':items,'rounds':rounds,'profile':p,'model':model_info()})

@login_required
@hospital_only
def upload(request):
    metric=None; error=None
    if request.method=='POST' and request.FILES.get('dataset'):
        f=request.FILES['dataset']; p=request.user.profile
        try:
            round_no=FederatedRound.objects.filter(status='OPEN').order_by('-round_no').first()
            if not round_no:
                last=FederatedRound.objects.order_by('-round_no').first(); n=(last.round_no+1 if last else 1)
                round_no=FederatedRound.objects.create(round_no=n)
            result=train_local_model(f,p.client_id or request.user.username,round_no.round_no)
            sub=Submission.objects.create(hospital=request.user,filename=f.name,records=result['records'],accuracy=result['accuracy'],macro_f1=result['macro_f1'],trees=result['trees'],status='TRAINED',round_no=round_no.round_no,model_version=model_info()['version'])
            metric=sub
            messages.success(request,'Local model trained successfully. You can now submit it to the federated round.')
        except Exception as exc: error=str(exc)
    return render(request,'hospital/upload.html',{'metric':metric,'error':error,'model':model_info()})

@login_required
@hospital_only
def federated(request):
    p=request.user.profile
    open_round=FederatedRound.objects.filter(status='OPEN').order_by('-round_no').first()
    if request.method=='POST':
        sub=Submission.objects.filter(hospital=request.user,status='TRAINED').order_by('-created_at').first()
        if not sub: messages.error(request,'Train a local model first.'); return redirect('hospital_federated')
        sub.status='SUBMITTED'; sub.round_no=open_round.round_no if open_round else sub.round_no; sub.save()
        messages.success(request,'Local model update submitted to the simulated FL server.')
        return redirect('hospital_federated')
    subs=Submission.objects.filter(hospital=request.user).order_by('-created_at')
    return render(request,'hospital/federated.html',{'items':subs,'round':open_round,'model':model_info()})

@login_required
@hospital_only
def client_portal(request, client_id):
    if request.user.profile.client_id != client_id: return redirect('hospital_dashboard')
    return render(request,'hospital/client.html',{'client_id':client_id,'profile':request.user.profile,'model':model_info()})

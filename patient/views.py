from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Prediction
from services.ml_service import FEATURES, predict_one, model_info

FIELDS = {
'age':('Age','number'), 'age_normalized':('Age normalized','number'), 'bmi':('BMI','number'),
'HbA1c_level':('HbA1c level','number'), 'glucose':('Glucose','number'), 'cholesterol':('Cholesterol','number'),
'sleep_hours':('Sleep hours','number'), 'triglycerides':('Triglycerides','number'), 'blood_pressure':('Blood pressure','number'),
'crp_level':('CRP level','number'), 'homocysteine_level':('Homocysteine level','number'), 'systolic_bp':('Systolic BP','number'),
'diastolic_bp':('Diastolic BP','number'), 'alcohol_intake':('Alcohol intake','number'), 'salt_intake':('Salt intake','number'),
'heart_rate':('Heart rate','number'), 'hdl':('HDL','number'), 'ldl':('LDL','number'),
'age_level':('Age level','select'),'gender':('Gender','select'),'bmi_level':('BMI level','select'),'smoking':('Smoking','select'),
'physical_activity':('Physical activity','select'),'family_history':('Family history','select'),'stress_level':('Stress level','select'),
'low_hdl_cholesterol':('Low HDL cholesterol','select'),'high_ldl_cholesterol':('High LDL cholesterol','select'),
'high_blood_pressure':('High blood pressure','select'),'sugar_consumption':('Sugar consumption','select'),
'education_level':('Education level','select'),'employment_status':('Employment status','select')}
OPTIONS={
'age_level':['Young','Adult','Middle','Senior'],'gender':['Female','Male'],'bmi_level':['Underweight','Normal','Overweight','Obese'],
'smoking':['Never','Former','Current'],'physical_activity':['Low','Moderate','High'],'family_history':['No','Yes'],
'stress_level':['Low','Moderate','High'],'low_hdl_cholesterol':['No','Yes'],'high_ldl_cholesterol':['No','Yes'],
'high_blood_pressure':['No','Yes'],'sugar_consumption':['Low','Moderate','High'],'education_level':['Primary','Secondary','Tertiary'],
'employment_status':['Student','Employed','Self-employed','Unemployed']}

@login_required
def dashboard(request):
    history=Prediction.objects.filter(patient=request.user)[:8]
    return render(request,'patient/dashboard.html',{'history':history,'model':model_info()})

@login_required
def predict(request):
    result=None; error=None; probs={}
    if request.method=='POST':
        try:
            payload={}
            for key in FEATURES:
                value=request.POST.get(key,'')
                if key in OPTIONS: payload[key]=value
                else: payload[key]=float(value)
            label,confidence,probs=predict_one(payload)
            Prediction.objects.create(patient=request.user,prediction=label,confidence=confidence,probabilities=probs,input_snapshot=payload,model_version=model_info()['version'])
            result={'label':label,'confidence':confidence,'probs':probs}
        except Exception as exc:
            error=str(exc)
    return render(request,'patient/predict.html',{'result':result,'error':error,'fields':FIELDS,'options':OPTIONS,'model':model_info()})

@login_required
def history(request):
    return render(request,'patient/history.html',{'items':Prediction.objects.filter(patient=request.user)})

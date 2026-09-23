from pathlib import Path
import copy, joblib, pandas as pd
from django.conf import settings
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from .ml_service import FEATURES, load_model, clear_model_cache

LOCAL_TREES = 60
UPLOAD_DIR = Path(settings.MEDIA_ROOT) / 'local_models'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def train_local_model(csv_file, client_id, round_no):
    df = pd.read_csv(csv_file)
    missing=[c for c in FEATURES+['sublabel'] if c not in df.columns]
    if missing: raise ValueError('Missing columns: ' + ', '.join(missing))
    df=df.dropna(subset=FEATURES+['sublabel']).copy()
    if len(df)<20: raise ValueError('At least 20 valid records are required.')
    bundle=load_model(); pre=copy.deepcopy(bundle['pipeline'].named_steps['preprocessor'])
    encoder=bundle['label_encoder']
    X=df[FEATURES]; y=encoder.transform(df['sublabel'].astype(str))
    Xtr,Xte,ytr,yte=train_test_split(X,y,test_size=.2,random_state=42,stratify=y)
    Xtrp=pre.transform(Xtr); Xtep=pre.transform(Xte)
    rf=RandomForestClassifier(n_estimators=LOCAL_TREES,max_features='sqrt',min_samples_leaf=2,bootstrap=True,random_state=42+round_no,n_jobs=-1)
    rf.fit(Xtrp,ytr); pred=rf.predict(Xtep)
    acc=float(accuracy_score(yte,pred)); f1=float(f1_score(yte,pred,average='macro'))
    path=UPLOAD_DIR/f'{client_id}_round_{round_no}.joblib'
    joblib.dump({'rf':rf,'records':len(df),'accuracy':acc,'macro_f1':f1,'client_id':client_id,'round_no':round_no},path,compress=3)
    return {'records':len(df),'accuracy':acc,'macro_f1':f1,'trees':LOCAL_TREES,'path':str(path)}

def aggregate(round_no, submissions):
    """Simulated secure-style tree aggregation: only local tree estimators are combined.
    Raw training rows are not used by this function. This is a deployment demo, not cryptographic secure aggregation.
    """
    bundles=[joblib.load(s['path']) for s in submissions]
    if len(bundles)<1: raise ValueError('No local models available.')
    base=copy.deepcopy(bundles[0]['rf'])
    trees=[]
    for b in bundles: trees.extend(b['rf'].estimators_)
    trees=trees[:len(submissions)*LOCAL_TREES]
    base.estimators_=trees
    base.n_estimators=len(trees)
    global_bundle=load_model()
    new_bundle=copy.deepcopy(global_bundle)
    new_bundle['pipeline'].named_steps['classifier']=base
    new_bundle['model_version']=f'v{round_no+1}.0.0'
    out=Path(settings.MEDIA_ROOT)/f'global_model_round_{round_no}.joblib'
    joblib.dump(new_bundle,out,compress=3)
    clear_model_cache()
    return str(out), len(trees)

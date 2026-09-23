# Federated Healthcare — Complete Django Prototype

A deployable academic prototype for **Federated Machine Learning for Chronic Disease Prediction**.

## What is included

- Patient portal
  - 31-feature prediction form
  - Real trained Random Forest model (`ml_models/chronic_disease_rf.joblib`)
  - Prediction probabilities and confidence
  - Prediction history
- Three hospital client portals
  - Hospital 1 / Hospital 2 / Hospital 3 demo accounts
  - CSV upload
  - Local 60-tree Random Forest training
  - Local accuracy and macro-F1
  - Model-update submission
- Admin portal
  - Patient/prediction monitoring
  - Hospital submissions
  - Federated round status
  - Three-client tree aggregation action
- PostgreSQL support through `DATABASE_URL`
- SQLite fallback for local development
- Render deployment configuration (`render.yaml`)
- The latest Synthetic V2 dataset used for the verified baseline
- The trained model artifact used by the Patient Portal

## Verified baseline

The supplied model was trained with the same 80/10/10 stratified split and Random Forest configuration used in the project experiment:

- Dataset: `Synthetic_Chronic_Disease_4Class_90_93pct.csv`
- Records: 119,784
- Classes: `DI`, `DI_HY`, `HY`, `N`
- Raw input features: 31
- Processed features: 55
- Random Forest trees: 180
- Test accuracy: **92.68%**
- Test balanced accuracy: **92.68%**
- Test macro F1: **92.68%**

The dataset is **synthetic/controlled benchmark data** and is not a clinical dataset. The application is not a medical diagnostic system.

## Architecture

```text
                         PATIENT PORTAL
                               |
                               v
                         Django Backend
                               |
                   active global model
          (latest FL artifact, or bundled baseline)
                               |
                 preprocessing + 180-tree RF
                               |
                    DI / DI_HY / HY / N

 HOSPITAL 1 ---- local 60-tree model ----\
 HOSPITAL 2 ---- local 60-tree model ----- > simulated FL aggregation
 HOSPITAL 3 ---- local 60-tree model ----/              |
                                                       v
                                                global model version
                                                       |
                                                       +----> Patient inference

                         ADMIN PORTAL
              users / predictions / FL rounds
```

## Important FL prototype limitation

The hospital upload workflow in this repository is a **simulation** of a federated deployment. For a convenient web demo, uploaded CSVs are processed by the Django service. The aggregation step combines Random Forest tree estimators rather than performing cryptographic secure aggregation.

For the final research implementation, the local trainer should run inside each hospital environment and communicate only approved model updates through Flower/SuperLink or an equivalent federated orchestration layer. Do not describe this repository as providing differential privacy or cryptographic secure aggregation unless those mechanisms are separately implemented.

## Local run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

### Demo accounts

| Portal | Username | Password |
|---|---|---|
| Patient | `patient` | `patient123` |
| Hospital 1 | `hospital1` | `hospital123` |
| Hospital 2 | `hospital2` | `hospital123` |
| Hospital 3 | `hospital3` | `hospital123` |
| Admin | `admin` | `admin123` |

Change these credentials before using the app outside a demo.

## Render deployment

The repository contains `render.yaml` for a web service plus PostgreSQL.

1. Push the repository to GitHub.
2. In Render, create a Blueprint from the repository.
3. Render will build the Django service and PostgreSQL database from `render.yaml`.
4. Set `CSRF_TRUSTED_ORIGINS` to your HTTPS Render URL if prompted.
5. Deploy.
6. The build command installs dependencies, runs migrations, seeds demo accounts, and collects static files. The start command launches Gunicorn.

The included model is already bundled, so **Render does not need to retrain the 180-tree baseline during deployment**.

## GitHub note

The repository intentionally includes two large project artifacts:

- `data/Synthetic_Chronic_Disease_4Class_90_93pct.csv` (~50 MB)
- `ml_models/chronic_disease_rf.joblib` (~47 MB)

Both are below GitHub's 100 MB single-file limit. For long-term versioning of multiple model/data versions, Git LFS is recommended.

## Project structure

```text
federated_healthcare_complete/
├── accounts/                 # authentication, profiles, demo seeding
├── patient/                  # patient predictions/history
├── hospital/                 # hospital clients + FL submissions
├── admin_portal/             # system administration
├── services/                 # ML inference + simulated FL aggregation
├── ml_models/                # trained model artifact
├── data/                     # latest synthetic benchmark CSV
├── templates/                # frontend pages
├── static/css/               # responsive dark healthcare UI
├── config/                   # Django settings/URLs/WSGI
├── manage.py
├── requirements.txt
├── render.yaml
└── Procfile
```

## Model input schema

The Patient Portal uses these 31 legitimate model inputs:

**Numerical (18):** `age`, `age_normalized`, `bmi`, `HbA1c_level`, `glucose`, `cholesterol`, `sleep_hours`, `triglycerides`, `blood_pressure`, `crp_level`, `homocysteine_level`, `systolic_bp`, `diastolic_bp`, `alcohol_intake`, `salt_intake`, `heart_rate`, `hdl`, `ldl`.

**Categorical (13):** `age_level`, `gender`, `bmi_level`, `smoking`, `physical_activity`, `family_history`, `stress_level`, `low_hdl_cholesterol`, `high_ldl_cholesterol`, `high_blood_pressure`, `sugar_consumption`, `education_level`, `employment_status`.

The trained pipeline stores the preprocessing stage and classifier together, so Django accepts the raw 31 fields.


## Active global model behavior

Patient inference automatically uses the newest `media/global_model_round_<N>.joblib` artifact when a completed aggregation has created one. If no aggregated artifact exists, the bundled `ml_models/chronic_disease_rf.joblib` baseline is used. The model cache is invalidated after aggregation so subsequent predictions in the running service pick up the new global model.

**Render note:** files written to the default service filesystem are ephemeral. Aggregated model artifacts created at runtime can disappear after a restart or redeploy unless persistent storage/object storage is added. The bundled baseline remains available because it is part of the repository.

## Deployment-ready notes

- The patient prediction service automatically uses the newest `media/global_model_round_<N>.joblib` artifact when an FL round has been aggregated; otherwise it uses `ml_models/chronic_disease_rf.joblib` (v1 baseline).
- Render Python is pinned with `.python-version` to `3.13.5`.
- Put these project files at the GitHub repository root so `manage.py`, `requirements.txt`, and `render.yaml` are directly visible. No Render Root Directory is then required.
- Render's default filesystem is ephemeral. Runtime-generated global-model artifacts in `media/` do not survive a service replacement/redeploy unless durable storage is added. This is acceptable for the current FL demonstration; production persistence should use durable object storage or another persistent model registry.

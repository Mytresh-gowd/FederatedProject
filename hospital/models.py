from django.db import models
from django.contrib.auth.models import User

class Submission(models.Model):
    STATUS=[('READY','Ready'),('TRAINED','Local model trained'),('SUBMITTED','Submitted to FL round'),('AGGREGATED','Included in global model')]
    hospital=models.ForeignKey(User,on_delete=models.CASCADE,related_name='submissions')
    filename=models.CharField(max_length=255)
    records=models.PositiveIntegerField(default=0)
    accuracy=models.FloatField(null=True,blank=True)
    macro_f1=models.FloatField(null=True,blank=True)
    trees=models.PositiveIntegerField(default=0)
    status=models.CharField(max_length=30,choices=STATUS,default='READY')
    round_no=models.PositiveIntegerField(default=0)
    model_version=models.CharField(max_length=50,default='v1.0.0')
    created_at=models.DateTimeField(auto_now_add=True)

class FederatedRound(models.Model):
    STATUS=[('OPEN','Open'),('COMPLETED','Completed')]
    round_no=models.PositiveIntegerField(unique=True)
    clients=models.PositiveIntegerField(default=0)
    trees_per_client=models.PositiveIntegerField(default=60)
    global_trees=models.PositiveIntegerField(default=180)
    status=models.CharField(max_length=20,choices=STATUS,default='OPEN')
    global_accuracy=models.FloatField(null=True,blank=True)
    global_macro_f1=models.FloatField(null=True,blank=True)
    global_model_version=models.CharField(max_length=50,default='v1.0.0')
    created_at=models.DateTimeField(auto_now_add=True)
    completed_at=models.DateTimeField(null=True,blank=True)

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Profile
from hospital.models import FederatedRound

USERS=[
 ('patient','patient123','PATIENT','Demo Patient',''),
 ('hospital1','hospital123','HOSPITAL','Hospital 1','HOSPITAL-1'),
 ('hospital2','hospital123','HOSPITAL','Hospital 2','HOSPITAL-2'),
 ('hospital3','hospital123','HOSPITAL','Hospital 3','HOSPITAL-3'),
 ('admin','admin123','ADMIN','System Admin',''),
]
class Command(BaseCommand):
    help='Create safe demo accounts for the deployed prototype.'
    def handle(self,*args,**kwargs):
        for username,password,role,name,client in USERS:
            u,created=User.objects.get_or_create(username=username,defaults={'first_name':name})
            u.set_password(password); u.is_staff=(role=='ADMIN'); u.save()
            Profile.objects.update_or_create(user=u,defaults={'role':role,'organization':name if role=='HOSPITAL' else 'Federated Healthcare Demo','client_id':client})
        FederatedRound.objects.get_or_create(round_no=1,defaults={'clients':3,'global_trees':180,'global_accuracy':0.9263711495,'global_macro_f1':0.9263784260,'status':'OPEN'})
        self.stdout.write(self.style.SUCCESS('Demo accounts and initial FL round are ready.'))

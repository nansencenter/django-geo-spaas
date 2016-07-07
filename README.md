Nansen-Cloud - GeoDjango Apps for satellite data management
===========================================================

Instructions for adding new data to nansen-cloud (relative to a nersc-vagrant installation DIR)  

1. Install nersc-vagrant, following https://github.com/nansencenter/nersc-vagrant  
 cd $DIR  
 git clone https://github.com/nansencenter/nersc-vagrant  
 cd nersc-vagrant  
 vagrant up develop (cf. only "vagrant up" at https://github.com/nansencenter/nersc-vagrant)  

2. Optional aliases for your virtual machine (done inside the virtual machine and at the top level)  
 vagrant ssh develop  
 vi .bashrc  
 alias   vib='vi ~/.bash_aliases'  
 alias   lst='ls --color=auto --indicator-style=none -al'  
 alias   lss='ls --color=auto --indicator-style=none -C'  
 alias    ls='ls --color=auto --indicator-style=none -aC'  
 alias  clid='cd /home/vagrant/shared/develop_vm/nansen-cloud; lst'  
 alias  clic='cd /home/vagrant/shared/develop_vm/nansen-cloud/nansencloud/ingest_gnssr; lst'  
 alias  iipp='clid ; python project/manage.py shell'  
 alias   iip='ipython'  
 alias  giff='echo ; echo git difftool -y -t kdiff3                            ; echo ; git difftool -y -t kdiff3                       ; echo'  
 alias  gitd='echo ; echo git log --diff-filter=D --summary , grep delete      ; echo ; git log --diff-filter=D --summary | grep delete ; echo'  
 alias  gitl='echo ; echo git rev-parse --short HEAD                           ; echo ; git rev-parse --short HEAD                      ; echo'  
 alias  gitm='echo ; echo git checkout master                                  ; echo ; git checkout master                             ; echo'  
 alias  gitn='echo ; echo git checkout \!*                                     ; echo ; git checkout \!*                                ; echo'  
 alias  gits='echo ; echo git status, git branch -a                            ; echo ; git status ; echo ; git branch -a               ; echo'  
 alias  gitt='echo ; echo git tag -n                                           ; echo ; git tag -n                                      ; echo'  
 alias  glog='echo ; echo git log --pretty=format:"%h - %an, %ar : %s" --graph ; echo ; git log --pretty=format:"%h - %an, %ar : %s" --graph | more -22'  
 PS1='${debian_chroot:+($debian_chroot)}\[\033[01;34m\]\w\[\033[00m\] \$ '  
 exit (leave both vi and the virtual machine)  

3. Create an "ingest_newdata" repo branch and copy an existing subdir as the template for adding new data (outside the virtual machine)  
 cd $DIR/nersc-vagrant/shared/develop_vm/nansen-cloud  
 git checkout develop ; git checkout -b ingest_newdata  
 cd $DIR/nersc-vagrant/shared/develop_vm/nansen-cloud/nansencloud  
 cp -r ingest_lance_buoys ingest_newdata  

4. Edit the files in ingest_newdata (not shown) and add the new data to the list (outside the virtual machine)  
 cd $DIR/nersc-vagrant/shared/develop_vm/nansen-cloud/project/project  
 vi settings.py                    (and augment the list of INSTALLED_APPS with 'nansencloud.ingest_newdata',)  

5. Perform a unit test and perhaps a migration (inside the virtual machine)  
 vagrant ssh develop  
 cd /vagrant/shared/develop_vm/nansen-cloud/project  
 python manage.py test nansencloud.ingest_newdata  
 python manage.py makemigrations  

6. Clean up the repo and commit the branch  
 cd  
 git add .  
 git commit -m "added GNSS-R ingest"  

Notes: See the wiki page for more details.  

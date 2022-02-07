#!/bin/sh
cd /home/daniel/A2A_MAS
git add -A
git commit -a -m "update from vmware"
eval "$(ssh-agent -s)"
ssh-add home/daniel/.ssh/strapi_ssh
git push origin main
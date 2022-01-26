#cd /home/cuongtv/strapi/
git add -A
git commit -a -m "update from vmware"
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/strapi_ssh
git push origin main
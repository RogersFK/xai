# xai

git rm --cached -r api/uploads
echo "api/uploads/" >> .gitignore
git add .gitignore
git commit -m "Remove uploads from repo"
git push origin dev --force

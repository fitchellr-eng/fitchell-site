#!/bin/bash
# Выкладка robertfitchell.ru на training-vps (Новосибирск).
# Запуск с Mac:  bash ~/Desktop/Проекты/fitchell-site/deploy/deploy.sh
set -e

SRC="/Users/De_Colt/Desktop/Проекты/fitchell-site/"
HOST="training-vps"
DEST="/var/www/robertfitchell/"

rsync -az --delete \
  --exclude '.git' --exclude '.claude' --exclude 'deploy' \
  --exclude 'cloud-function' --exclude 'CNAME' --exclude 'skills-lock.json' \
  --exclude '.DS_Store' --exclude '.gitignore' \
  --exclude 'audit' \
  --exclude 'audit-preview-*' \
  "$SRC" "$HOST:$DEST"

# права выставляем на сервере: старый rsync с Mac тащит сюда локальные права
ssh "$HOST" 'chown -R www-data:www-data /var/www/robertfitchell \
  && find /var/www/robertfitchell -type d -exec chmod 755 {} + \
  && find /var/www/robertfitchell -type f -exec chmod 644 {} + \
  && nginx -t && systemctl reload nginx'
echo "Выложено: https://robertfitchell.ru"

#!/usr/bin/env bash
# Deploy exact product identity checks with private backups and rollback.
set -Eeuo pipefail
umask 077
SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CONTAINER=mainbuyer-automation-n8n-1
ID=W10R01EvidenceResearch
exec 9>"$HOME/.urbansky-live-stack-mainbuyer2.lock"
flock -n 9 || exit 75
# Do not interrupt running executions with the required n8n restart.
RUNNING="$(docker exec -i mainbuyer-automation-postgres-1 sh -c 'psql -X -At -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1' <<'SQL'
SELECT COUNT(*) FROM execution_entity WHERE status IN ('running','new');
SQL
)"
[[ "$RUNNING" == 0 ]] || { echo "Active n8n executions; retry deployment when idle." >&2; exit 75; }
mkdir -p "$HOME/.urbansky-backups"
BACKUP="$(mktemp -d "$HOME/.urbansky-backups/w10-research-recovery.XXXXXX")"
IMPORT_DIR="$(docker exec "$CONTAINER" mktemp -d /tmp/urbansky-w10-research-recovery.XXXXXX)"
trap 'docker exec "$CONTAINER" rm -rf "$IMPORT_DIR" >/dev/null 2>&1 || true' EXIT
docker exec "$CONTAINER" n8n export:workflow --id="$ID" --output="$IMPORT_DIR/before.json" >/dev/null
docker cp "$CONTAINER:$IMPORT_DIR/before.json" "$BACKUP/before.json" >/dev/null
python3 "$SOURCE/automation/scripts/patch_research_recovery.py" "$BACKUP/before.json" "$BACKUP/after.json"
ACTIVE="$(python3 - "$BACKUP/before.json" <<'PY'
import sys,json
print('1' if json.load(open(sys.argv[1]))[0]['active'] else '0')
PY
)"
if cmp -s "$BACKUP/before.json" "$BACKUP/after.json"; then
 echo "W10_RESEARCH_RECOVERY_ALREADY_INSTALLED BACKUP=$BACKUP"
 exit 0
fi
copy_import() { docker exec -i "$CONTAINER" sh -c 'umask 077; cat > "$1"' sh "$IMPORT_DIR/$2" < "$1"; }
rollback() {
 trap - ERR
 copy_import "$BACKUP/before.json" rollback.json
 docker exec "$CONTAINER" n8n unpublish:workflow --id="$ID" >/dev/null 2>&1 || true
 docker exec "$CONTAINER" n8n import:workflow --input="$IMPORT_DIR/rollback.json" >/dev/null
 if [[ "$ACTIVE" == 1 ]]; then docker exec "$CONTAINER" n8n publish:workflow --id="$ID" >/dev/null; fi
 docker restart "$CONTAINER" >/dev/null
 echo "W10_RESEARCH_RECOVERY_ROLLBACK BACKUP=$BACKUP" >&2
}
copy_import "$BACKUP/after.json" after.json
trap 'rc=$?; rollback; exit "$rc"' ERR
docker exec "$CONTAINER" n8n unpublish:workflow --id="$ID" >/dev/null
docker exec "$CONTAINER" n8n import:workflow --input="$IMPORT_DIR/after.json" >/dev/null
if [[ "$ACTIVE" == 1 ]]; then docker exec "$CONTAINER" n8n publish:workflow --id="$ID" >/dev/null; fi
docker restart "$CONTAINER" >/dev/null
ready=0
for _ in $(seq 1 30); do
 if docker exec "$CONTAINER" node -e "fetch('http://127.0.0.1:5678/healthz',{signal:AbortSignal.timeout(5000)}).then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))" >/dev/null 2>&1; then ready=1;break;fi
 sleep 2
done
test "$ready" = 1
docker exec "$CONTAINER" n8n export:workflow --id="$ID" --output="$IMPORT_DIR/verified.json" >/dev/null
docker cp "$CONTAINER:$IMPORT_DIR/verified.json" "$BACKUP/verified.json" >/dev/null
python3 - "$BACKUP/after.json" "$BACKUP/verified.json" <<'PY'
import json,sys
before,after=(json.load(open(p))[0] for p in sys.argv[1:])
assert all(before.get(k)==after.get(k) for k in ('id','name','active','nodes','connections','settings'))
print('W10_RESEARCH_RECOVERY_DEPLOY_VERIFIED')
PY
trap - ERR
echo "W10_RESEARCH_RECOVERY_BACKUP=$BACKUP"

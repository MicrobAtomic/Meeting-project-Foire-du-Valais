#!/bin/sh
# Environment file must be private and controlled by the operator.
set -eu
: "${CLUB_APP_DIR:?Set CLUB_APP_DIR to the deployed application directory}"
: "${CLUB_ENV_FILE:?Set CLUB_ENV_FILE to the private environment file}"
case "${1:-}" in
  process_notifications|expire_guest_access) ;;
  *) echo "Usage: run-job.sh process_notifications|expire_guest_access [options]" >&2; exit 64 ;;
esac
cd "$CLUB_APP_DIR"
set -a
. "$CLUB_ENV_FILE"
set +a
exec "$CLUB_APP_DIR/.venv/bin/python" "$CLUB_APP_DIR/manage.py" "$@"

#!/bin/bash

DEPOTDOWNLOADER="{ddexe}"
INSTALL_DIR=""
APP_ID=""
BRANCH=""
VALIDATE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    +force_install_dir)
      INSTALL_DIR="$2"
      shift 2
      ;;
    +login)
      if [[ "$2" == "anonymous" ]]; then
        shift 2
      else
        echo "ERROR Steam login unsupported"
        exit 1
      fi
      ;;
    +app_update)
      APP_ID="$2"
      shift 2
      ;;
    -beta)
      BRANCH="$2"
      shift 2
      ;;
    validate)
      VALIDATE=true
      shift 1
      ;;
    +quit)
      shift 1
      break
      ;;
    *)
      echo "ERROR Unknown argument: $1"
      exit 1
      ;;
  esac
done

[[ -n "$APP_ID" ]] || exit 0
CMD=("$DEPOTDOWNLOADER" "-app" "$APP_ID" "-dir" "$INSTALL_DIR")
if [[ -n "$BRANCH" ]]; then
  CMD+=("-branch" "$BRANCH")
fi
if $VALIDATE; then
  CMD+=("-validate")
fi

echo "START ${CMD[*]}"
exec "${CMD[@]}"
echo "END ${DEPOTDOWNLOADER} (exit code: ${?})"
find $INSTALL_DIR -type f \( -name "*.sh" -o -name "*.x86_64" -o ! -name "*.*" \) -exec chmod 744 {} +

exit 0

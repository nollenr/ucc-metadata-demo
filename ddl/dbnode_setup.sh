#!/usr/bin/env bash
# fanout_crdb_update.sh
# - Loads SETCRDBVARS from ~/.bashrc to define CRDBNODE{1..N}
# - Copies & runs prep_update.sh on all nodes
# - Copies apply_update.sh to all nodes, then runs it on all EXCEPT the last node

set -Eeuo pipefail

# ---- Config (override with env if you like) ----------------------------------
REMOTE_USER="${REMOTE_USER:-ec2-user}"
REMOTE_DIR="${REMOTE_DIR:-/home/${REMOTE_USER}}"
SSH_OPTS="${SSH_OPTS:- -o BatchMode=yes -o StrictHostKeyChecking=accept-new }"
SCP_OPTS="${SCP_OPTS:- -o StrictHostKeyChecking=accept-new }"

PREP="./prep_update.sh"
APPLY="./apply_update.sh"

# ---- Load CRDBNODE* by running SETCRDBVARS -----------------------------------
load_nodes() {
  # Source .bashrc in the *current* shell (not a subshell) with -u temporarily off
  if [[ -r "${HOME}/.bashrc" ]]; then
    set +u
    # shellcheck disable=SC1090
    source "${HOME}/.bashrc" >/dev/null 2>&1 || true
    set -u
  fi

  if declare -F SETCRDBVARS >/dev/null 2>&1; then
    # Function is available locally; run it here so CRDBNODE* exist in this shell
    SETCRDBVARS >/dev/null 2>&1 || true
  else
    # Fallback: use an interactive bash to load rc + run function,
    # then print *shell* variables (not env) as export lines for import here.
    eval "$(
      bash -ic '
        set +u
        source ~/.bashrc >/dev/null 2>&1 || true
        type SETCRDBVARS >/dev/null 2>&1 && SETCRDBVARS >/dev/null 2>&1 || true
        set -u
        for v in $(compgen -A variable | grep -E "^CRDBNODE[0-9]+$" | sort -V); do
          printf "export %s=%q\n" "$v" "${!v}"
        done
      ' || true
    )"
  fi

  # Collect CRDBNODE variable *names* from this shell, e.g., CRDBNODE1..N
  mapfile -t NODE_VARS < <(compgen -A variable | grep -E '^CRDBNODE[0-9]+$' | sort -V)

  if ((${#NODE_VARS[@]} == 0)); then
    echo "ERROR: No CRDBNODE* variables found after running SETCRDBVARS." >&2
    exit 1
  fi
}


# ---- Helpers -----------------------------------------------------------------
copy_to_host() {
  local host="$1" file="$2"
  scp ${SCP_OPTS} "$file" "${REMOTE_USER}@${host}:${REMOTE_DIR}/"
}

run_on_host() {
  local host="$1" cmd="$2"
  # Use a login shell; temporarily disable -u while sourcing remote rc
  ssh ${SSH_OPTS} "${REMOTE_USER}@${host}" \
    "bash -lc 'set +u; source ~/.bashrc >/dev/null 2>&1 || true; set -u; ${cmd}'"
}

# ---- Main --------------------------------------------------------------------
main() {
  load_nodes

  # Make scripts executable locally
  chmod +x "${PREP}"
  chmod +x "${APPLY}"

  # Indirect expansion to read each variable's value
  hosts=()
  for var in "${NODE_VARS[@]}"; do
    hosts+=( "${!var}" )
  done

  echo "Discovered ${#hosts[@]} nodes:"
  printf '  - %s\n' "${hosts[@]}"  

  # 1) prep_update.sh: copy + run on ALL nodes
  echo "==> Distributing and running ${PREP} on ALL nodes..."
  for host in "${hosts[@]}"; do
    echo "[${host}] copy ${PREP}"
    copy_to_host "${host}" "${PREP}"
    echo "[${host}] run ${PREP}"
    run_on_host "${host}" "chmod +x '${REMOTE_DIR}/$(basename "$PREP")' && '${REMOTE_DIR}/$(basename "$PREP")'"
  done

  # 2) apply_update.sh: copy to ALL, run on all EXCEPT LAST
  echo "==> Distributing ${APPLY} to ALL nodes..."
  for host in "${hosts[@]}"; do
    echo "[${host}] copy ${APPLY}"
    copy_to_host "${host}" "${APPLY}"
  done

  echo "==> Running ${APPLY} on all EXCEPT the last node..."
  last_index=$(( ${#hosts[@]} - 1 ))
  for i in "${!hosts[@]}"; do
    host="${hosts[$i]}"
    if [[ $i -eq $last_index ]]; then
      echo "[${host}] (skipping APPLY on last node)"
      continue
    fi
    echo "[${host}] run ${APPLY}"
    run_on_host "${host}" "chmod +x '${REMOTE_DIR}/$(basename "$APPLY")' && '${REMOTE_DIR}/$(basename "$APPLY")'"
  done

  echo "All done."
}

main "$@"

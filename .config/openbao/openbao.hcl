# =====================================================================
# OpenBao server — openbao.hcl
# Workstation: primo (Arch Linux) · generated 2026-09-28
#
# Canonical filename/format: openbao.hcl (HCL; JSON also accepted).
# Single-node Raft workstation template: TLS-only loopback listener,
# integrated Raft storage, file audit device, default Shamir seal.
# Load with: bao server -config=/home/phaedrus/.config/openbao/openbao.hcl
#
# Researched from official upstream docs on 2026-09-28:
#   Top-level reference:
#   https://github.com/openbao/openbao/blob/HEAD/website/content/docs/configuration/index.mdx
#   Raft storage backend:
#   https://github.com/openbao/openbao/blob/HEAD/website/content/docs/configuration/storage/raft.mdx
#   TCP listener:
#   https://github.com/openbao/openbao/blob/HEAD/website/content/docs/configuration/listener/tcp.mdx
#   Telemetry:
#   https://github.com/openbao/openbao/blob/HEAD/website/content/docs/configuration/telemetry.mdx
#   Audit stanza:
#   https://github.com/openbao/openbao/blob/HEAD/website/content/docs/configuration/audit.mdx
#   User lockout:
#   https://github.com/openbao/openbao/blob/HEAD/website/content/docs/configuration/user-lockout.mdx
#   Seal stanza (auto-unseal + health-check options):
#   https://github.com/DingJun1028/openbao/blob/8d648cab5992950080a64e9cb3c3516bd56fc897/website/content/docs/configuration/seal/index.mdx
#   Common file-audit device options:
#   https://openbao.org/docs/audit/
#
# A directory of *.hcl/*.json files is also accepted: files load in
# alphabetical order, last scalar wins, list blocks (listener/audit)
# are appended.
# =====================================================================

# ---------------------------------------------------------------------
# Top-level options (alphabetical).
# ---------------------------------------------------------------------

# ELI5: allow audit devices that use the `prefix` option (lets operators
# write semi-arbitrary content into the audit log). Keep false; only
# enable temporarily when you need a prefixed device.
allow_audit_log_prefixing = false

# ELI5: allow unauthenticated workflow executions. Keep false.
allow_unauthenticated_workflows = false

# ELI5: the address advertised to other cluster nodes for client
# redirection, and used for plugin backends. Also settable via
# BAO_API_ADDR. Should point at the listener address below.
api_addr = "https://127.0.0.1:8200"

# ELI5: read-cache size for the physical storage layer, in NUMBER OF
# ENTRIES (not bytes) — note this is a string. Bigger = more RAM for
# faster reads.
cache_size = "131072"

# ELI5: address advertised for server-to-server cluster traffic.
# Required with the raft backend. Also settable via BAO_CLUSTER_ADDR.
# OpenBao ignores the scheme; cluster traffic always uses TLS.
cluster_addr = "https://127.0.0.1:8201"

# ELI5: a human name for the cluster. Empty = OpenBao generates one.
cluster_name = ""

# ELI5: default lifetime for tokens/secrets ("768h" = 32 days).
# Must not exceed max_lease_ttl. Duration labels like "30s", "1h".
default_lease_ttl = "768h"

# ELI5: how long a single request may run before OpenBao cancels it.
# A listener's max_request_duration overrides this per-listener.
default_max_request_duration = "90s"

# ELI5: comma-separated internal mutexes to watch for deadlocks
# ("statelock", "quotas", "expiration"). Empty = off. Costs performance.
detect_deadlocks = ""

# ELI5: turn off ALL caches (huge performance hit). Keep false.
disable_cache = false

# ELI5: turn off clustering/request-forwarding on the active node.
# MUST stay false when storage is raft (the docs forbid true here).
disable_clustering = false

# ELI5: disable single-use "SSCT" tokens (default true — they have
# limited utility; index headers are preferred instead).
disable_ssct_tokens = true

# ELI5: let standby nodes answer read-only requests. Keep false on a
# single node (there are no standbys anyway).
disable_standby_reads = false

# ELI5: add an X-Vault-Hostname response header naming the node that
# served the request (best effort). Off keeps responses minimal.
enable_response_header_hostname = false

# ELI5: add an X-Vault-Raft-Node-ID response header. Only emitted when
# actually running Raft; omitted otherwise even if enabled.
enable_response_header_raft_node_id = false

# ELI5: skip counting leases by role when no role-based quotas exist.
# true = less bookkeeping, but lease counts restart at 0 if you later
# enable a role quota.
imprecise_lease_role_tracking = false

# ELI5: enable the sys/internal/inspect endpoint (root/sudo only).
# Powerful debugging, keep off unless you need it.
introspection_endpoint = false

# ELI5: log file path (equivalent to the -log-file CLI flag).
# Empty = log to stderr.
log_file = ""

# ELI5: log format (equivalent to -log-format). Empty = default text
# format; "json" gives JSON lines.
log_format = ""

# ELI5: verbosity: trace, debug, info, warn, error. Also settable via
# BAO_LOG_LEVEL; SIGHUP with a valid value overrides both.
log_level = "info"

# ELI5: log rotation knobs (equivalents of -log-rotate-bytes,
# -log-rotate-duration, -log-rotate-max-files). Zeros/empty = rotation
# effectively off; logs go to stderr under systemd's journal.
log_rotate_bytes    = 0
log_rotate_duration = ""
log_rotate_max_files = 0

# ELI5: the longest lease any mount may hand out ("768h" = 32 days).
# Individual mounts can lower it via auth/secrets tune.
max_lease_ttl = "768h"

# ELI5: file to write the server PID into. Empty = don't write one.
pid_file = ""

# ELI5: automatically download plugins from OCI images. Keep false —
# auto-fetching code is a supply-chain risk.
plugin_auto_download = false

# ELI5: automatically register downloaded plugins. Default true.
plugin_auto_register = true

# ELI5: directory plugins may be loaded from. Empty = no plugin dir.
# Must be readable by OpenBao and may not be a symlink.
plugin_directory = ""

# ELI5: whether a failed plugin download is fatal ("fail") or ignored.
plugin_download_behavior = "fail"

# ELI5: expected octal permissions of plugin dirs/binaries, only used
# when the BAO_ENABLE_FILE_PERMISSIONS_CHECK file-permissions check is
# on. Empty = check disabled.
plugin_file_permissions = ""

# ELI5: expected owning uid of plugin dirs/binaries, same check as
# above. 0 = root-owned expectation.
plugin_file_uid = 0

# ELI5: enable the sys/raw endpoint (decrypt/encrypt raw barrier data).
# Highly privileged — keep false.
raw_storage_endpoint = false

# ELI5: serve the built-in web UI at /ui on the listener. Also settable
# via BAO_UI.
ui = true

# ELI5: allow creating audit devices via the API. Keep false; toggle
# temporarily via SIGHUP only when needed.
unsafe_allow_api_audit_creation = false

# NOTE: disable_mlock is deliberately absent. It appears in some
# third-party examples, but it is NOT in the official OpenBao server
# configuration reference (checked 2026-09-28), so setting it here
# would be inventing an option.

# ---------------------------------------------------------------------
# storage "raft": integrated Raft backend (alphabetical options).
# ---------------------------------------------------------------------

# ELI5: OpenBao's own built-in replicated storage — no external
# database needed. Every node keeps a full copy, writes need a quorum.
storage "raft" {
  # ELI5: how often Raft autopilot picks up membership changes
  # (promotions, unhealthy/dead nodes).
  autopilot_reconcile_interval = "10s"
  # ELI5: how often autopilot polls OpenBao for the data above.
  autopilot_update_interval = "2s"
  # ELI5: biggest single Raft log entry in bytes (default 1 MiB = 2x
  # the internal chunk size). Oversized puts fail.
  max_entry_size = 1048576
  # ELI5: biggest transactional Raft entry in bytes (default 8 MiB =
  # 16x the chunk size); each op inside must still fit max_entry_size.
  max_transaction_size = 8388608
  # ELI5: this node's name in the Raft cluster. Also settable via
  # BAO_RAFT_NODE_ID.
  node_id = "primo"
  # ELI5: where Raft keeps its data (raft.db etc.). Also settable via
  # BAO_RAFT_PATH.
  path = "/home/phaedrus/.local/share/openbao/raft"
  # ELI5: scales Raft's internal timing. 0 (or omitted) = default
  # timing, currently equal to 5 — tuned for small servers. 1 = fastest
  # (recommended for production), 10 = max. Lower = faster failure
  # detection at the cost of more network/CPU.
  performance_multiplier = 0
  # ELI5: join via retry_join as a non-voting member (gets data, no
  # quorum vote — read scaling). Only valid with a retry_join stanza.
  retry_join_as_non_voter = false
  # ELI5: minimum Raft log entries between snapshots/truncations
  # (default 8192). Raise only if disk IO from truncation storms hurts.
  snapshot_threshold = 8192
  # ELI5: how often each node checks whether log truncation is due
  # (default 120s; minimum 5ms). Nodes stagger randomly up to 2x.
  snapshot_interval = "120s"
  # ELI5: log entries kept on disk after truncation (default 10000).
  # Only raise if followers can't catch up under heavy write load.
  trailing_logs = 10000

  # retry_join blocks (leader_api_addr / auto_join / TLS options) are
  # how extra nodes find the cluster. Single node here, so none —
  # see the raft docs URL in the header for the full stanza.
}

# ha_storage: deliberately absent. With the raft backend a separate
# ha_storage "cannot be declared" (official docs) — Raft already
# provides HA coordination.

# ---------------------------------------------------------------------
# listener "tcp": the API listener (alphabetical options).
# ---------------------------------------------------------------------

listener "tcp" {
  # ELI5: where to listen. Loopback-only: only this machine reaches it.
  # go-sockaddr templates (e.g. {{ GetPrivateIP }}) are allowed.
  address = "127.0.0.1:8200"
  # ELI5: bind address for cluster server-to-server traffic. Defaults
  # to one port above address; set explicitly here.
  cluster_address = "127.0.0.1:8201"

  # ELI5: custom HTTP response headers, keyed by status code
  # ("default" = all responses; "2xx"/"301" etc. = specific ones).
  # Each maps header names to lists of values. OMITTED here = none
  # (the default). NOTE: the official docs illustrate this block with
  # QUOTED keys ("default" = {...}), but quoted attribute names are
  # not valid HCL — attribute names must be bare identifiers — so an
  # empty header map is expressed by omitting the block entirely.
  # Headers with an X-Vault- prefix are rejected (reserved).

  # ELI5: kill the legacy UNAUTHENTICATED /sys/rekey/* endpoints.
  # Default true since v2.5.0 — leaving them open is a security risk.
  disable_unauthed_rekey_endpoints = true
  # ELI5: kill the legacy unauthenticated /sys/generate-root/*
  # endpoints (attackers could cancel your root generation).
  # Default true since v2.5.3.
  disable_unauthed_generate_root_endpoints = true

  # ELI5: HTTP timeouts. idle = keep-alive wait (falls back to
  # read_timeout, then read_header_timeout if zero). write "0" =
  # infinity (the default).
  http_idle_timeout        = "5m"
  http_read_header_timeout = "10s"
  http_read_timeout        = "30s"
  http_write_timeout       = "0"

  # ELI5: per-listener cap overriding default_max_request_duration.
  max_request_duration = "90s"
  # ELI5: cap on estimated RAM for a parsed JSON request body
  # (default 32 MiB + 512 KiB; 0 = default; negative = unlimited).
  max_request_json_memory = 34078720
  # ELI5: max strings (keys+values) in a JSON request body
  # (default 1000; 0 = default; negative = unlimited).
  max_request_json_strings = 1000
  # ELI5: hard cap on request size in bytes (default 32 MiB; 0 =
  # default; negative = unlimited).
  max_request_size = 33554432

  # ELI5: PROXY protocol (v1) handling for when a load balancer fronts
  # OpenBao. Empty = disabled. If enabled you MUST also set
  # proxy_protocol_authorized_addrs (non-empty) — omitted here because
  # the protocol is off; values: use_always | allow_authorized |
  # deny_unauthorized.
  proxy_protocol_behavior = ""
  # proxy_protocol_authorized_addrs: required-if-enabled, so absent
  # while proxy_protocol_behavior is "".

  # ELI5: metrics endpoint hardening. All false here = /v1/sys/metrics
  # stays authenticated, enabled, serving every endpoint, on its
  # default path. See the docs example for a dedicated metrics-only
  # listener pattern (metrics_only + disallow_metrics split).
  telemetry {
    disallow_metrics             = false
    metrics_only                 = false
    metrics_path                 = ""
    unauthenticated_metrics_access = false
  }

  # ELI5: Go profiling endpoints. Keep unauthenticated access off —
  # pprof data helps attackers profile the server.
  profiling {
    unauthenticated_pprof_access = false
    # NOTE: the docs also describe an in-flight-requests endpoint, but
    # the reference disagrees with its own example on the option name
    # (unauthenticated_in_flight_requests_access vs
    # unauthenticated_in_flight_request_access), so it is left unset
    # rather than guessed. Either way the default is false (off).
  }

  # --- ACME (automatic TLS certificates) ---
  # ELI5: when tls_cert_file is empty, OpenBao can fetch certificates
  # via ACME instead. We pin real cert files below, so ACME is
  # explicitly DISABLED by emptying its directory URL.
  tls_acme_alpn_challenge_port  = 443
  tls_acme_ca_directory         = ""
  tls_acme_ca_root              = ""
  tls_acme_cache_path           = "~/.local/share/certmagic"
  tls_acme_challenge_host       = ""
  tls_acme_disable_alpn_challenge = false
  tls_acme_disable_http_challenge = false
  tls_acme_domains              = []
  tls_acme_eab_key_id           = ""
  tls_acme_eab_mac_key          = ""
  tls_acme_email                = ""
  tls_acme_http_challenge_port  = 80
  tls_acme_test_ca_directory    = ""

  # --- TLS ---
  # ELI5: watch the cert/key files and reload automatically on change
  # (for cert-manager style rotation). Off; SIGHUP also reloads them.
  tls_auto_reload          = false
  tls_auto_reload_interval = "30s"
  # ELI5: PEM certificate (concatenate server cert + CA chain, server
  # first if you need clients to trust it) and private key. PROVISION
  # THESE BEFORE STARTING — e.g. a local CA or mkcert pair. Paths are
  # re-read on SIGHUP (the startup-time values win).
  tls_cert_file = "/home/phaedrus/.config/openbao/tls/tls.crt"
  tls_key_file  = "/home/phaedrus/.config/openbao/tls/tls.key"
  # ELI5: cipher suite list, comma-separated. Only consulted for TLS
  # 1.2 and below — we run TLS 1.3-only, so this stays empty/unused.
  tls_cipher_suites = ""
  # ELI5: CA used to verify CLIENT certificates (mTLS). Empty = mTLS
  # off (see the two string flags below).
  tls_client_ca_file = ""
  # ELI5: "false" (string!) = TLS stays ON. You must opt in to
  # plaintext with "true" — OpenBao assumes TLS by default.
  tls_disable = "false"
  # ELI5: "false" (string) = ask clients for a cert if they have one
  # (optional client-cert auth). Mutually exclusive with
  # tls_require_and_verify_client_cert — never set both "true".
  tls_disable_client_certs = "false"
  # ELI5: which key-exchange groups the server offers. This is the
  # docs' "enforce PQC" set: hybrid post-quantum KEMs (X25519+ML-KEM
  # etc.) so key exchange resists future quantum decryption. Go
  # prefers PQC automatically when both sides support it; listing only
  # these ENFORCES it (non-PQC clients will fail to connect).
  tls_key_exchange_preferences = ["X25519MLKEM768", "SecP256r1MLKEM768", "SecP384r1MLKEM1024", "MLKEM1024"]
  # NOTE: tls_prefer_server_cipher_suites is deprecated and has no
  # effect — deliberately not set.
  # ELI5: TLS 1.3 only, both directions. tls10/tls11 are documented as
  # widely considered insecure.
  tls_max_version = "tls13"
  tls_min_version = "tls13"
  # ELI5: "false" (string) = do NOT require client certs. "true" would
  # turn on mandatory mTLS against the system CAs / tls_client_ca_file.
  tls_require_and_verify_client_cert = "false"

  # --- X-Forwarded-For ---
  # ELI5: trusting X-Forwarded-For is OFF (authorized_addrs empty).
  # Only enable behind a load balancer you control, listing its IPs.
  x_forwarded_for_authorized_addrs       = ""
  x_forwarded_for_hop_skips              = "0"
  x_forwarded_for_reject_not_authorized  = "true"
  x_forwarded_for_reject_not_present     = "true"
}

# ---------------------------------------------------------------------
# audit "file": declarative file audit device (two labels: type, path).
# ---------------------------------------------------------------------

# ELI5: every request/response is written to this tamper-evident log.
# Declarative devices are (re)created on restarts and SIGHUP; the path
# label ("local") must be unique. If NO audit device can write, OpenBao
# stops answering requests (fail closed) — keep the disk healthy.
audit "file" "local" {
  description = "Local file audit device (workstation)."

  # ELI5: device options are all strings. file_path = where (or
  # "stdout"); mode = log file permissions; format = "json" (the only
  # valid value); hmac_accessor = hash token accessors (keep true);
  # log_raw = log secrets UNHASHED (keep false!); prefix = custom line
  # prefix (needs allow_audit_log_prefixing=true since v2.3.2, empty =
  # none); elide_list_responses = drop list bodies from the log;
  # skip_test = "true" skips the mount-time write probe (dangerous —
  # a dead device would then block unsealing instead of failing fast).
  options = {
    file_path            = "/home/phaedrus/.local/state/openbao/audit.log"
    mode                 = "0600"
    format               = "json"
    hmac_accessor        = "true"
    log_raw              = "false"
    prefix               = ""
    elide_list_responses = "false"
    skip_test            = ""
  }
}

# ---------------------------------------------------------------------
# user_lockout: brute-force backoff for password logins.
# ---------------------------------------------------------------------

# ELI5: after this many bad password attempts, the account can't try
# again for lockout_duration; the counter resets after
# lockout_counter_reset with no attempts (or on a successful login).
# Stanza names: "all" (shown here) or per-method: userpass, ldap,
# approle — per-method settings win over "all". Only those three auth
# methods support lockout. Values are the documented defaults
# (5 attempts / 15m / 15m); the feature is on by default and can be
# disabled per-method with disable_lockout or globally via the
# BAO_DISABLE_USER_LOCKOUT env var.
user_lockout "all" {
  lockout_threshold     = "5"
  lockout_duration      = "15m"
  lockout_counter_reset = "15m"
  disable_lockout       = false
}

# ---------------------------------------------------------------------
# telemetry: metrics publishing (alphabetical options).
# ---------------------------------------------------------------------

# ELI5: where OpenBao sends operational metrics. Everything below is
# disabled/empty except the in-memory Prometheus endpoint
# (/v1/sys/metrics?format=prometheus, needs a token with read+list on
# it) which keeps 24h of history. Point one *_address at your collector
# to actually ship metrics somewhere.
telemetry {
  # --- Common ---
  # ELI5: break the lease-expiry gauge down by namespace too (default
  # false — it can explode metric cardinality).
  add_lease_metrics_namespace_labels = false
  # ELI5: don't prefix gauges with the hostname (recommended true when
  # enable_hostname_label is used instead).
  disable_hostname = false
  # ELI5: add a `host` label with the hostname to every metric.
  enable_hostname_label = false
  # ELI5: allow metrics not named by prefix_filter (true = allow all
  # when no filters; false + no filters = send nothing).
  filter_default = true
  # ELI5: width of the lease-expiration histogram buckets.
  lease_metrics_epsilon = "1h"
  # ELI5: max gauge label cardinality.
  maximum_gauge_cardinality = 500
  # ELI5: metric name prefix (default "vault", kept for continuity).
  metrics_prefix = "vault"
  # ELI5: number of lease-expiration buckets (168 x 1h = one week).
  num_lease_metrics_buckets = 168
  # ELI5: allow/block rules, e.g. ["+vault.token", "-vault.expire"].
  # More specific rules win; "-" wins ties.
  prefix_filter = []
  # ELI5: how often high-cardinality usage gauges (tokens, entities,
  # secrets) are collected; "none" disables.
  usage_gauge_period = "10m"

  # --- statsite / statsd ---
  statsite_address = ""
  statsd_address   = ""

  # --- Circonus ---
  circonus_api_app                   = "nomad"
  circonus_api_token                 = ""
  circonus_api_url                   = "https://api.circonus.com/v2"
  circonus_broker_id                 = ""
  circonus_broker_select_tag         = ""
  circonus_check_display_name        = ""
  circonus_check_force_metric_activation = false
  circonus_check_id                  = ""
  # ELI5: empty = default "<hostname>:<application>" (e.g.
  # "host123:nomad"); identifies this instance's metrics.
  circonus_check_instance_id         = ""
  # ELI5: empty = default "<service>:<application>" search tag.
  circonus_check_search_tag          = ""
  circonus_check_tags                = ""
  circonus_submission_interval       = "10s"
  circonus_submission_url            = ""

  # --- DogStatsD ---
  dogstatsd_addr = ""
  dogstatsd_tags = []

  # --- Prometheus ---
  # ELI5: how long metrics stay in memory for /v1/sys/metrics.
  # "0" would disable Prometheus telemetry.
  prometheus_retention_time = "24h"

  # --- Stackdriver ---
  stackdriver_debug_logs = false
  stackdriver_location   = ""
  stackdriver_namespace  = ""
  stackdriver_project_id = ""
}

# ---------------------------------------------------------------------
# Deliberately omitted blocks (documented, not needed on this node).
# ---------------------------------------------------------------------
# seal: absent = default Shamir seal (manual unseal with key shares on
#   every restart). Add a seal "<kms>" stanza for auto-unseal (HSM/cloud
#   KMS via plugin); since v2.7.0 many mechanisms are plugin-only
#   (plugin "kms" "<name>" + seal "<name>"). Seal health-check options
#   (health_check_enabled/health_check_timeout/health_check_interval/
#   health_check_interval_unhealthy) only apply inside a seal stanza.
# ha_storage: forbidden with the raft backend (see storage note above).
# initialize: one-time declarative self-initialization on first boot —
#   intentionally left to the operator, not the config file.
# plugin: declarative OCI plugin download/registration — none used.
# service_registration "kubernetes": not applicable on a workstation.

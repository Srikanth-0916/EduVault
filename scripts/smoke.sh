#!/usr/bin/env bash
# End-to-end smoke test for a running APAAR-SDMV stack.
#
#   docker compose up -d --build
#   ./scripts/smoke.sh
#
# All data is synthetic and every external integration is mock/sandbox.
set -euo pipefail

API_BASE="${API_BASE:-http://localhost:8000/api/v1}"
WEB_URL="${WEB_URL:-http://localhost:3000}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

pass() { printf 'PASS  %s\n' "$1"; }
fail() { printf 'FAIL  %s\n' "$1" >&2; exit 1; }

json_field() {
  python3 -c 'import json,sys; value=json.load(sys.stdin); print(value["'"$1"'"])'
}

status() {
  curl -sS -o "$WORK/body" -w '%{http_code}' "$@"
}

login() {
  local email="$1"
  local code
  code="$(status -X POST "$API_BASE/auth/login" \
    -H 'Content-Type: application/json' \
    -d "{\"email\":\"$email\",\"password\":\"Demo@1234\"}")"
  [ "$code" = "200" ] || fail "login $email returned $code: $(cat "$WORK/body")"
  json_field accessToken < "$WORK/body"
}

echo "== health and web =="
code="$(status "$API_BASE/health")"
[ "$code" = "200" ] || fail "health returned $code"
[ "$(json_field status < "$WORK/body")" = "ok" ] || fail "health payload is not ok"
pass "API health"

code="$(status -L "$WEB_URL/login")"
[ "$code" = "200" ] || fail "web login returned $code"
pass "web console reachable"

echo "== institution upload -> attest -> submit =="
OPERATOR="$(login operator@demo-ait.edu)"
NODAL="$(login nodal@demo-ait.edu)"
REVIEWER="$(login reviewer@aicte.demo)"
STUDENT="$(login student@demo-ait.edu)"

code="$(status -X POST "$API_BASE/submission-batches" \
  -H "Authorization: Bearer $OPERATOR" -H 'Content-Type: application/json' \
  -d '{"academicYear":"2026-27","sourceType":"CSV_UPLOAD"}')"
[ "$code" = "201" ] || fail "batch create returned $code: $(cat "$WORK/body")"
BATCH_ID="$(json_field id < "$WORK/body")"
pass "batch created ($BATCH_ID)"

code="$(status -X POST "$API_BASE/submission-batches/$BATCH_ID/file" \
  -H "Authorization: Bearer $OPERATOR" \
  -F "file=@data/demo/batch_valid.csv;type=text/csv")"
[ "$code" = "200" ] || fail "upload returned $code: $(cat "$WORK/body")"
pass "CSV uploaded"

code="$(status -X POST "$API_BASE/submission-batches/$BATCH_ID/validate" \
  -H "Authorization: Bearer $OPERATOR")"
[ "$code" = "200" ] || fail "validation returned $code: $(cat "$WORK/body")"
[ "$(json_field status < "$WORK/body")" = "READY_FOR_ATTESTATION" ] \
  || fail "batch not ready for attestation"
pass "validation ready for attestation"

code="$(status -X POST "$API_BASE/submission-batches/$BATCH_ID/attest" \
  -H "Authorization: Bearer $NODAL" -H 'Content-Type: application/json' \
  -d '{"declaration":true,"attestationName":"Nisha Kulkarni"}')"
[ "$code" = "200" ] || fail "attestation returned $code: $(cat "$WORK/body")"
pass "nodal attestation recorded"

code="$(status -X POST "$API_BASE/submission-batches/$BATCH_ID/submit" \
  -H "Authorization: Bearer $NODAL")"
[ "$code" = "200" ] || fail "submit returned $code: $(cat "$WORK/body")"
pass "batch submitted"

echo "== AICTE review =="
code="$(status -X POST "$API_BASE/submission-batches/$BATCH_ID/decision" \
  -H "Authorization: Bearer $REVIEWER" -H 'Content-Type: application/json' \
  -d '{"decision":"ACCEPT","reason":"Synthetic smoke review"}')"
[ "$code" = "200" ] || fail "decision returned $code: $(cat "$WORK/body")"
[ "$(json_field status < "$WORK/body")" = "ACCEPTED" ] || fail "batch was not accepted"
pass "reviewer accepted batch"

echo "== reporting export =="
ANALYST="$(login analyst@aicte.demo)"
code="$(status "$API_BASE/reports/enrolment/export.csv?groupBy=institution" \
  -H "Authorization: Bearer $ANALYST")"
[ "$code" = "200" ] || fail "report export returned $code: $(cat "$WORK/body")"
python3 -c 'import sys; body=open(sys.argv[1], encoding="utf-8").read().lower(); assert "student_name" not in body; assert "apaar" not in body' "$WORK/body" \
  || fail "report export contains a direct identifier"
pass "aggregate report CSV exported"

echo "== consent verification =="
code="$(status -X POST "$API_BASE/verification-requests" \
  -H "Authorization: Bearer $STUDENT" -H 'Content-Type: application/json' \
  -d '{"recipientName":"Acme HR","recipientOrg":"Acme Demo","recipientEmail":"hr@acme-demo.example","purpose":"Employment screening","requestedClaims":["INSTITUTION","PROGRAMME","ENROLMENT_STATUS"],"legalBasis":"CONSENT","expiresInHours":24}')"
[ "$code" = "201" ] || fail "verification request returned $code: $(cat "$WORK/body")"
REQUEST_ID="$(json_field id < "$WORK/body")"
pass "verification request created"

code="$(status -X POST "$API_BASE/verification-requests/$REQUEST_ID/authorize" \
  -H "Authorization: Bearer $STUDENT")"
[ "$code" = "200" ] || fail "authorize returned $code: $(cat "$WORK/body")"
TOKEN="$(json_field token < "$WORK/body")"
pass "consent link authorized"

code="$(status "$API_BASE/public/verify/$TOKEN")"
[ "$code" = "200" ] || fail "public verify returned $code: $(cat "$WORK/body")"
[ "$(json_field valid < "$WORK/body")" = "True" ] || fail "public claim was not valid"
python3 -c 'import json,sys; body=open(sys.argv[1]).read(); assert "123456789012" not in body' "$WORK/body" \
  || fail "raw APAAR leaked into public response"
pass "public verification shows authorized claims"

code="$(status -X POST "$API_BASE/verification-requests/$REQUEST_ID/revoke" \
  -H "Authorization: Bearer $STUDENT" -H 'Content-Type: application/json' \
  -d '{"reason":"Smoke test completed"}')"
[ "$code" = "200" ] || fail "revoke returned $code: $(cat "$WORK/body")"
code="$(status "$API_BASE/public/verify/$TOKEN")"
[ "$code" = "410" ] || fail "revoked token returned $code (expected 410)"
pass "revoked link returns generic 410"

echo "SMOKE PASS"

#!/usr/bin/env bash
# Génère une CA de développement + certificats serveur et client (mTLS).
# Usage : scripts/generate_certs.sh [dossier_de_sortie]   (défaut : certs/)
set -euo pipefail

OUT="${1:-certs}"
mkdir -p "$OUT"
cd "$OUT"

# 1. Autorité de certification (CA) qui signe les deux certificats
openssl req -x509 -newkey rsa:2048 -nodes -days 365 \
  -keyout ca.key -out ca.crt -subj "/CN=grpc-course-dev-ca" 2>/dev/null

# 2. Certificat serveur : les SAN doivent contenir le nom utilisé par le client
printf "subjectAltName=DNS:localhost,DNS:backend,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n" > server.ext
openssl req -newkey rsa:2048 -nodes -keyout server.key -out server.csr -subj "/CN=localhost" 2>/dev/null
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -days 365 -extfile server.ext -out server.crt 2>/dev/null

# 3. Certificat client (uniquement utile en mTLS)
printf "extendedKeyUsage=clientAuth\n" > client.ext
openssl req -newkey rsa:2048 -nodes -keyout client.key -out client.csr -subj "/CN=grpc-course-client" 2>/dev/null
openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -days 365 -extfile client.ext -out client.crt 2>/dev/null

rm -f ./*.csr ./*.ext ca.srl
echo "Certificats générés dans $(pwd)"

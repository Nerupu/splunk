#!/bin/bash
#set -x

if command -v openssl &> /dev/null; then
    openssl s_client -servername token.actions.githubusercontent.com -showcerts -connect token.actions.githubusercontent.com:443 < /dev/null 2>/dev/null | sed -ne '/-BEGIN CERTIFICATE-/,/-END CERTIFICATE-/p' | sed "0,/-END CERTIFICATE-/d" > certificate.crt
    thumbprint=`openssl x509 -in certificate.crt -fingerprint -noout | cut -f2 -d'=' | tr -d ':' | tr '[:upper:]' '[:lower:]'`
    rm certificate.crt
    echo $thumbprint
else
    echo "OpenSSL not installed"
fi
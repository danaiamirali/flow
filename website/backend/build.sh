#!/bin/bash
<<COMMENT
This build file is to generates a 
truststore.jks file, which is a key store for working with java applications. 

The truststore.jks file holds our certificate authority issued client cert for authenticating pyspark with kafka
COMMENT



# Validate the presence of required environment variables
if [ ! -f .env ]; then
    echo ".env file not found"
    exit 1
fi 

if [ -z "$CA_CERTIFICATE" ]; then
    echo "CA_CERTIFICATE environmental variable not set"
    exit 1
fi

if [ -z "$TRUSTSTORE_PASS" ]; then
    echo "TRUSTSTORE_PASS environmental variable not set"
    exit 1
fi

source .env


# Save the provided CA certificate to a file and import it into the truststore
echo "$CA_CERTIFICATE" > ca-certificate.crt

keytool -import \
    -trustcacerts \
    -alias do-ca \
    -file ca-certificate.crt \
    -keystore truststore.jks \
    -storepass "$TRUST_STORE_PASS" \
    -noprompt

echo "Truststore 'truststore.jks' created successfully."
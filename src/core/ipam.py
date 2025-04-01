from typing import Dict, List, Optional
import ipaddress
import socket
import threading
import time
import subprocess
from pathlib import Path
import json
import csv
import os

class IPAMEntry:
    """Represents a single IP address entry in the IPAM system."""
    def __init__(self, 
                 ip: str, 
                 subnet: str = "", 
                 hostname: str = "", 
                 description: str = "", 
                 status: str = "Unknown", 
                 session_name: str = ""):
        self.ip = ip
        self.subnet = subnet
        self.hostname = hostname
        self.description = description
        self.status = status  # Unknown, Active, Reserved, etc.
        self.session_name = session_name  # Link to a session if applicable
        self.last_seen = None
    
    def to_dict(self) -> Dict:
        """Convert entry to dictionary for serialization."""
        return {
            "ip": self.ip,
            "subnet": self.subnet,
            "hostname": self.hostname,
            "description": self.description,
            "status": self.status,
            "session_name": self.session_name,
            "last_seen": self.last_seen
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'IPAMEntry':
        """Create an IPAMEntry from dictionary data."""
        entry = cls(
            ip=data.get("ip", ""),
            subnet=data.get("subnet", ""),
            hostname=data.get("hostname", ""),
            description=data.get("description", ""),
            status=data.get("status", "Unknown"),
            session_name=data.get("session_name", "")
        )
        entry.last_seen = data.get("last_seen")
        return entry


class Subnet:
    """Represents a subnet in the IPAM system."""
    def __init__(self, 
                 cidr: str, 
                 name: str = "", 
                 description: str = ""):
        self.cidr = cidr
        self.name = name
        self.description = description
        self.network = ipaddress.ip_network(cidr, strict=False)
    
    def to_dict(self) -> Dict:
        """Convert subnet to dictionary for serialization."""
        return {
            "cidr": self.cidr,
            "name": self.name,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Subnet':
        """Create a Subnet from dictionary data."""
        return cls(
            cidr=data.get("cidr", ""),
            name=data.get("name", ""),
            description=data.get("description", "")
        )
    
    def get_ip_range(self) -> List[str]:
        """Get all usable IP addresses in this subnet."""
        # Skip network and broadcast addresses for IPv4
        if self.network.version == 4:
            return [str(ip) for ip in list(self.network.hosts())]
        # For IPv6, include all addresses
        return [str(ip) for ip in self.network]
    
    def get_usage_stats(self, entries: Dict[str, IPAMEntry]) -> Dict:
        """Calculate usage statistics for this subnet."""
        total = self.network.num_addresses
        # Subtract 2 for network and broadcast addresses in IPv4
        if self.network.version == 4 and total > 2:
            total -= 2
            
        used = sum(1 for ip in self.get_ip_range() if ip in entries)
        
        return {
            "total": total,
            "used": used,
            "available": total - used,
            "utilization": round((used / total) * 100, 2) if total > 0 else 0
        }


class IPAMManager:
    """Manages IP addresses and subnets."""
    def __init__(self, config, session_manager=None):
        self.config = config
        self.session_manager = session_manager
        
        # Set up file paths
        data_dir = Path(config.get("general", "data_dir", str(Path.home() / ".asshm")))
        self.ipam_dir = data_dir / "ipam"
        self.ipam_dir.mkdir(parents=True, exist_ok=True)
        
        self.entries_file = self.ipam_dir / "ip_entries.json"
        self.subnets_file = self.ipam_dir / "subnets.json"
        
        # Initialize data
        self.entries: Dict[str, IPAMEntry] = {}  # IP -> Entry
        self.subnets: Dict[str, Subnet] = {}     # CIDR -> Subnet
        
        self.load_data()
    
    def load_data(self):
        """Load IPAM data from storage."""
        # Load IP entries
        if self.entries_file.exists():
            try:
                with open(self.entries_file, 'r') as f:
                    entries_data = json.load(f)
                    for entry_data in entries_data:
                        entry = IPAMEntry.from_dict(entry_data)
                        self.entries[entry.ip] = entry
            except Exception as e:
                print(f"Error loading IPAM entries: {e}")
        
        # Load subnets
        if self.subnets_file.exists():
            try:
                with open(self.subnets_file, 'r') as f:
                    subnets_data = json.load(f)
                    for subnet_data in subnets_data:
                        subnet = Subnet.from_dict(subnet_data)
                        self.subnets[subnet.cidr] = subnet
            except Exception as e:
                print(f"Error loading IPAM subnets: {e}")
    
    def save_data(self):
        """Save IPAM data to storage."""
        # Save IP entries
        try:
            entries_data = [entry.to_dict() for entry in self.entries.values()]
            with open(self.entries_file, 'w') as f:
                json.dump(entries_data, f, indent=4)
        except Exception as e:
            print(f"Error saving IPAM entries: {e}")
        
        # Save subnets
        try:
            subnets_data = [subnet.to_dict() for subnet in self.subnets.values()]
            with open(self.subnets_file, 'w') as f:
                json.dump(subnets_data, f, indent=4)
        except Exception as e:
            print(f"Error saving IPAM subnets: {e}")
    
    def add_subnet(self, subnet: Subnet) -> bool:
        """Add a new subnet."""
        if subnet.cidr in self.subnets:
            return False
        
        self.subnets[subnet.cidr] = subnet
        self.save_data()
        return True
    
    def remove_subnet(self, cidr: str) -> bool:
        """Remove a subnet by CIDR."""
        if cidr not in self.subnets:
            return False
        
        # Remove entries associated with this subnet
        entries_to_remove = [ip for ip, entry in self.entries.items() 
                             if entry.subnet == cidr]
        for ip in entries_to_remove:
            self.entries.pop(ip, None)
        
        # Remove the subnet
        self.subnets.pop(cidr)
        self.save_data()
        return True
    
    def add_ip_entry(self, entry: IPAMEntry) -> bool:
        """Add a new IP entry."""
        self.entries[entry.ip] = entry
        self.save_data()
        return True
    
    def remove_ip_entry(self, ip: str) -> bool:
        """Remove an IP entry."""
        if ip not in self.entries:
            return False
        
        self.entries.pop(ip)
        self.save_data()
        return True
    
    def get_entry(self, ip: str) -> Optional[IPAMEntry]:
        """Get an entry by IP address."""
        return self.entries.get(ip)
    
    def get_subnet(self, cidr: str) -> Optional[Subnet]:
        """Get a subnet by CIDR."""
        return self.subnets.get(cidr)
    
    def find_subnet_for_ip(self, ip: str) -> Optional[Subnet]:
        """Find which subnet contains the given IP."""
        try:
            ip_obj = ipaddress.ip_address(ip)
            for subnet in self.subnets.values():
                if ip_obj in subnet.network:
                    return subnet
        except ValueError:
            pass  # Invalid IP format
        return None
    
    def scan_subnet(self, cidr: str, callback=None) -> List[str]:
        """Scan a subnet for active hosts using ping."""
        if cidr not in self.subnets:
            return []
        
        subnet = self.subnets[cidr]
        active_ips = []
        
        def ping_host(ip, results):
            """Ping a single host and record if active."""
            # Use platform-specific ping command
            if os.name == 'nt':  # Windows
                ping_cmd = ['ping', '-n', '1', '-w', '500', ip]
            else:  # Unix/Linux/MacOS
                ping_cmd = ['ping', '-c', '1', '-W', '1', ip]
            
            try:
                subprocess.check_output(ping_cmd, stderr=subprocess.STDOUT)
                results.append(ip)
                
                # Update entry in our database
                if ip in self.entries:
                    self.entries[ip].status = "Active"
                    self.entries[ip].last_seen = time.time()
                else:
                    # Create new entry
                    entry = IPAMEntry(ip=ip, subnet=cidr, status="Active")
                    entry.last_seen = time.time()
                    try:
                        # Try to get hostname
                        hostname = socket.gethostbyaddr(ip)[0]
                        entry.hostname = hostname
                    except socket.herror:
                        pass
                    self.entries[ip] = entry
                
                if callback:
                    callback(ip, True)
            except subprocess.CalledProcessError:
                if callback:
                    callback(ip, False)
        
        # Get all IPs in subnet
        ip_range = subnet.get_ip_range()
        
        # Use threading to speed up scanning
        threads = []
        for ip in ip_range:
            thread = threading.Thread(target=ping_host, args=(ip, active_ips))
            thread.daemon = True
            threads.append(thread)
            thread.start()
            
            # Limit number of concurrent threads
            while sum(t.is_alive() for t in threads) >= 50:
                time.sleep(0.1)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        self.save_data()
        return active_ips
    
    def import_from_csv(self, file_path: str) -> Dict:
        """Import IP data from CSV file."""
        added_ips = 0
        added_subnets = 0
        errors = 0
        
        try:
            with open(file_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        # Check if it's a subnet entry
                        if 'cidr' in row and row['cidr']:
                            subnet = Subnet(
                                cidr=row['cidr'],
                                name=row.get('name', ''),
                                description=row.get('description', '')
                            )
                            if self.add_subnet(subnet):
                                added_subnets += 1
                        
                        # Check if it's an IP entry
                        elif 'ip' in row and row['ip']:
                            entry = IPAMEntry(
                                ip=row['ip'],
                                subnet=row.get('subnet', ''),
                                hostname=row.get('hostname', ''),
                                description=row.get('description', ''),
                                status=row.get('status', 'Unknown'),
                                session_name=row.get('session_name', '')
                            )
                            if self.add_ip_entry(entry):
                                added_ips += 1
                    except Exception:
                        errors += 1
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
        
        return {
            "success": True,
            "added_ips": added_ips,
            "added_subnets": added_subnets,
            "errors": errors
        }
    
    def export_to_csv(self, file_path: str, include_ips: bool = True, include_subnets: bool = True) -> bool:
        """Export IPAM data to CSV file."""
        try:
            with open(file_path, 'w', newline='') as f:
                if include_subnets and self.subnets:
                    # Export subnets
                    writer = csv.DictWriter(f, fieldnames=["cidr", "name", "description"])
                    writer.writeheader()
                    for subnet in self.subnets.values():
                        writer.writerow({
                            "cidr": subnet.cidr,
                            "name": subnet.name,
                            "description": subnet.description
                        })
                    
                    # Add a blank line between sections
                    if include_ips:
                        f.write("\n")
                
                if include_ips and self.entries:
                    # Export IP entries
                    writer = csv.DictWriter(f, fieldnames=[
                        "ip", "subnet", "hostname", "description", 
                        "status", "session_name", "last_seen"
                    ])
                    writer.writeheader()
                    for entry in self.entries.values():
                        writer.writerow(entry.to_dict())
            
            return True
        except Exception as e:
            print(f"Error exporting IPAM data: {e}")
            return False 
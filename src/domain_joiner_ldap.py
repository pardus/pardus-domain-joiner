import ldap

class LDAP:
    def __init__(self, address, username, password):
        self.address = address
        self.username = username
        self.password = password
        self.conn = None

    def _connect(self):
        """Private method to establish the LDAP connection."""
        try:
            self.conn = ldap.initialize(f"ldap://{self.address}")
            self.conn.protocol_version = 3
            self.conn.set_option(ldap.OPT_REFERRALS, 0)
        except ldap.LDAPError as e:
            print(f"Failed to initialize LDAP connection: {e}")
            self.conn = None

    def authenticate(self):
        """Authenticate the user with the provided credentials."""
        if self.conn is None:
            self._connect()

        try:
            self.conn.simple_bind_s(self.username, self.password)
            print("LDAP authentication successful!")
            return True
        except ldap.LDAPError as e:
            print(f"LDAP error: {e}")
            return False
        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    def check_computer_exists_in_ad(self, hostname):
        """Check if the given hostname already exists in Active Directory."""
        if not self.authenticate():
            return False

        try:
            domain_controller = self._build_domain_controller()
            search_base = domain_controller
            search_filter = f"(cn={hostname})"

            result = self.conn.search_s(search_base, ldap.SCOPE_SUBTREE, search_filter)

            if result:
                for dn, entry in result:
                    if dn and entry:
                        print(f"Hostname {hostname} already exists in Active Directory!")
                        # print(f"Found dn: {dn}")
                        # print(f"Found entry: {entry}")
                        return entry
                    else:
                        print(f"Hostname {hostname} is available to use.")
                        return None
        except ldap.LDAPError as e:
            print(f"LDAP search failed: {e}")
            return None
        finally:
            self._unbind_connection()

    def _build_domain_controller(self):
        """Build the domain controller string from the LDAP address."""
        domain_parts = self.address.split(".")
        return ",".join([f"dc={part}" for part in domain_parts])

    def _unbind_connection(self):
        """Close the LDAP connection."""
        if self.conn:
            self.conn.unbind_s()
            print("Connection closed.")
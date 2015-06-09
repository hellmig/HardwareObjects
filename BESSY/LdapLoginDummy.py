from HardwareRepository.BaseHardwareObjects import Procedure
import logging
import ldap

"""
<procedure class="LdapLogin">
  <ldaphost>ldaphost.mydomain</ldaphost>
  <ldapport>389</ldapport>
</procedure>
"""

###
### Checks the proposal password in a LDAP server
###
### Dummy validates every username with arbitrary password
###
class LdapLoginDummy(Procedure):
    def __init__(self,name):
        Procedure.__init__(self,name)
        self.ldapConnection=None

    # Initializes the hardware object
    def init(self):
        pass

    # Creates a new connection to LDAP if there's an exception on the current connection
    def reconnect(self):
        pass
            
    # Logs the error message (or LDAP exception) and returns the respective tuple
    def cleanup(self,ex=None,msg=None):
        msg="generic LDAP error"
        return (False,msg)

    # Check password in LDAP
    def login(self,username,password,retry=True):
        logging.getLogger("HWR").debug("LdapLoginDummy: validating %s" % username)
        return (True,username)

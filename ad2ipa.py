#! /usr/bin/python

# import json
import csv
import os
import string
import random
import subprocess
import sys
import ldap
import ldap.filter
from ldap.controls import SimplePagedResultsControl
from distutils.version import LooseVersion

# Check if we're using the Python "ldap" 2.4 or greater API
LDAP24API = LooseVersion(ldap.__version__) >= LooseVersion('2.4')

# If you're talking to LDAP, you should be using LDAPS for security!
LDAPSERVER = 'ldap://192.168.1.100'
BASEDN = 'DC=company,DC=name'
LDAPUSER = 'CN=user admin,DC=company,DC=name'
LDAPPASSWORD = 'userPassword123'
PAGESIZE = 100
# MAPPING = {'title':'title', 'givenName':'givenName', 'sn':'sn', 'cn':'cn', 'name':'gecos', 'displayName':'displayName', 'physicalDeliveryOfficeName':'employeeType', 'company':'userClass', 'telephoneNumber':'telephonenumber', 'streetAddress':'street', 'l':'l', 'st':'st', 'postalCode':'postalCode', 'department':'ou', 'employeeID':'employeeNumber', 'sAMAccountName':'uid'}
ATTRLIST = ['title', 'givenName', 'sn', 'cn', 'name', 'displayName', 'physicalDeliveryOfficeName', 'company', 'telephoneNumber', 'streetAddress', 'l', 'st', 'postalCode', 'department', 'employeeID', 'sAMAccountName']
usernames = ['username1', 'username2']
group = "usergroupname"

# expand users with error during the insertion to freeipa into this array
notAddedUsers = []
result_pages = 0
# expand all users into this array
all_results = []

def insert_user(attributes):
    pwd = "password123"
	
	# generate ipa command with attributes from Active Directory
    username = attributes['sAMAccountName'][0]
    addUserCommand = "ipa user-add " + username
	
    if 'givenName' in attributes:
        firstname = attributes['givenName'][0]
        addUserCommand += " --first \"" + firstname + "\""

    if 'sn' in attributes:
        lastname = attributes['sn'][0]
        addUserCommand += " --last \"" + lastname + "\""

    if 'displayName' in attributes:
        displayname = attributes['displayName'][0]
        addUserCommand += " --displayname \"" + displayname + "\""

    if 'name' in attributes:
        gecos = attributes['name'][0]
        addUserCommand += " --gecos \"" + gecos + "\""

    if 'streetAddress' in attributes:
        street = attributes['streetAddress'][0]
        addUserCommand += " --street \"" + street + "\""

    if 'l' in attributes:
        city = attributes['l'][0]
        addUserCommand += " --city \"" + city + "\""

    if 'st' in attributes:
        state = attributes['st'][0]
        addUserCommand += " --state \"" + state + "\""

    if 'postalCode' in attributes:
        postalcode = attributes['postalCode'][0]
        addUserCommand += " --postalcode " + postalcode

    if 'telephoneNumber' in attributes:
        phone = attributes['telephoneNumber'][0]
        addUserCommand += " --phone \"" + phone + "\""

    if 'title' in attributes:
        title = attributes['title'][0]
        addUserCommand += " --title \"" + title + "\""

    if 'department' in attributes:
        orgunit = attributes['department'][0]
        addUserCommand += " --orgunit \"" + orgunit + "\""

    if 'employeeID' in attributes:
        employeenumber = attributes['employeeID'][0]
        addUserCommand += " --employeenumber " + employeenumber

    if 'physicalDeliveryOfficeName' in attributes:
        employeetype = attributes['physicalDeliveryOfficeName'][0]
        addUserCommand += " --employeetype \"" + employeetype + "\""


 #   addUserCommand = ("ipa user-add " + username + \
 #                             " --first " + firstname + \
 #                             " --last " + firstname + \
 #                             " --displayname \"" + displayname + "\"" + \
 #                             " --gecos \"" + gecos + "\"" + \
 #                             " --street \"" + street + "\"" + \
 #                             " --city \"" + city + "\"" + \
 #                             " --state \"" + state + "\"" + \
 #                             " --postalcode " + postalcode + \
 #                             " --phone \"" + phone + "\"" + \
 #                             " --orgunit \"" + orgunit + "\"" + \
 #                             " --title \"" + title + "\"" + \
 #                             " --class \"" + userClass + "\"" + \
 #                             " --employeenumber " + employeenumber + \
 #                             " --employeetype \"" + employeetype + "\"")
    setUserPassCommand = ("ipa passwd " + username + " " + pwd)
   # print addUserCommand
    try:
        subprocess.check_output(addUserCommand, stderr=subprocess.STDOUT, shell=True)
        subprocess.check_output(setUserPassCommand, stderr=subprocess.STDOUT, shell=True)
       # subprocess.call(setUserPassCommand, shell=True)
        try:
            setUserRoleCommand = ("ipa group-add-member '" + group.strip() + "' --user " + username)
            subprocess.check_output(setUserRoleCommand, stderr=subprocess.STDOUT, shell=True)
           # print(username + " has been added to the group: " + group.strip())
        except(subprocess.CalledProcessError):
           # print("WARNING!!! " + username + " not added to " + group.strip())
            print(username + " created successfully")
    except subprocess.CalledProcessError as e:
        print('LDAP search failed: %s' % e)
        print("WARNING!!!! " + username)
        notAddedUsers.append(username)

def create_controls(pagesize):
    """Create an LDAP control with a page size of "pagesize"."""
    # Initialize the LDAP controls for paging. Note that we pass ''
    # for the cookie because on first iteration, it starts out empty.
    if LDAP24API:
        return SimplePagedResultsControl(True, size=pagesize, cookie='')
    else:
        return SimplePagedResultsControl(ldap.LDAP_CONTROL_PAGE_OID, True, (pagesize,''))

def get_pctrls(serverctrls):
    """Lookup an LDAP paged control object from the returned controls."""
    # Look through the returned controls and find the page controls.
    # This will also have our returned cookie which we need to make
    # the next search request.
    if LDAP24API:
        return [c for c in serverctrls
                if c.controlType == SimplePagedResultsControl.controlType]
    else:
        return [c for c in serverctrls
                if c.controlType == ldap.LDAP_CONTROL_PAGE_OID]

def set_cookie(lc_object, pctrls, pagesize):
    """Push latest cookie back into the page control."""
    if LDAP24API:
        cookie = pctrls[0].cookie
        lc_object.cookie = cookie
        return cookie
    else:
        est, cookie = pctrls[0].controlValue
        lc_object.controlValue = (pagesize,cookie)
        return cookie

# print attributes from Active Directory for debugging before insertion to free-ipa
def print_attrs(dn, attrs):
    for ele in attrs:
        print attrs[ele][0]

# Ignore server side certificate errors (assumes using LDAPS and
# self-signed cert). Not necessary if not LDAPS or it's signed by a real CA.
ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW)
# Don't follow referrals
ldap.set_option(ldap.OPT_REFERRALS, 0)

l = ldap.initialize(LDAPSERVER)
# Paged results only apply to LDAP v3
l.protocol_version = 3
try:
    # Bind/authenticate with a user with apropriate rights to add objects
    l.simple_bind_s(LDAPUSER, LDAPPASSWORD)
except ldap.LDAPError as e:
    exit('LDAP bind failed: %s' % e)

# Create the page control to work from
lc = create_controls(PAGESIZE)

for username in usernames:
    print username
    SEARCHFILTER = ldap.filter.filter_format('(&(objectClass=user)(sAMAccountName=%s))', [username])
	# Do searches until we run out of "pages" to get from the LDAP server.
    while True:
		# Send search request
		try:
			# If you leave out the ATTRLIST it'll return all attributes
			# which you have permissions to access. You may want to adjust
			# the scope level as well (perhaps "ldap.SCOPE_SUBTREE or ldap.SCOPE_ONELEVEL", but
			# it can reduce performance if you don't need it).
			msgid = l.search_ext(BASEDN, ldap.SCOPE_SUBTREE, SEARCHFILTER, ATTRLIST, serverctrls=[lc])
		except ldap.LDAPError as e:
			sys.exit('LDAP search failed: %s' % e)

		# Pull the results from the search request
		try:
			rtype, rdata, rmsgid, serverctrls = l.result3(msgid)
			all_results.extend(rdata)
			result_pages += 1
		except ldap.LDAPError as e:
			sys.exit('Could not pull LDAP results: %s' % e)

		# Each "rdata" is a tuple of the form (dn, attrs), where dn is
		# a string containing the DN (distinguished name) of the entry,
		# and attrs is a dictionary containing the attributes associated
		# with the entry. The keys of attrs are strings, and the associated
		# values are lists of strings.
		for dn, attrs in rdata:
		#    print_attrs(dn, attrs)
			insert_user(attrs)

		# Get cookie for next request
		pctrls = get_pctrls(serverctrls)
		if not pctrls:
			print >> sys.stderr, 'Warning: Server ignores RFC 2696 control.'
			break

		# Ok, we did find the page control, yank the cookie from it and
		# insert it into the control for our next search. If however there
		# is no cookie, we are done!
		cookie = set_cookie(lc, pctrls, PAGESIZE)
		if not cookie:
			break

# Clean up
l.unbind_s()

print('Received %d results in %d pages and %d errors.' % (len(all_results),result_pages,len(notAddedUsers)))

# Done!
sys.exit(0)
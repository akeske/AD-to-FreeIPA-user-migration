# AD-to-FreeIPA-user-migration
Migrate users from Active Directory to FreeIPA

![Python Version](https://img.shields.io/badge/python-2.7-green.svg)

### What is the purpose of this tool
The main goal of this script is to migrate users from Active Directory(AD Microsoft) to FreeIPA

### Attributed mapping
| FreeIPA aatributes  | AD attributes |
| ------------- | ------------- |
| title   | title   |
| givenname  | givenName  |
| sn  | sn  |
| cn  | cn  |
| displayName  | displayName  |
| initials  | initials  |
| gecos  | name  |
| mail  | mail  |
| telephonenumber  | telephonenumber  |
| street  | **streetAddress**  |
| l  | l  |
| st  | st  |
| postalCode  | postalCode  |
| ou  | **department**  |
| employeeNumber  | **employeeID `custom attr`**  |
| dn  | **distinguishedName**  |
| uid  | **sAMAccountName**  |

### How to use it
+ You have to edit the script, change the below variables
    * usernames `the array of users, sAMAccountName`
    * group `the secutiry group name that you want to add the new users`
    * LDAPSERVER
    * BASEDN
    * LDAPUSER
    * LDAPPASSWORD
+ execute the command
```bash
$ python ad2ipa.py
```

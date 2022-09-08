# Ansilbe Library

My modules for Ansible:

## postconf 

set Postfix configuration using native postconf utility in main.cf.

usage:

```
vars:
  # state = present is deafult. It is set in task.
  postfix_main:
    - name: myhostname
      value: mail.example.com
      state: present
    - name: mydomain
      value: mail.example.com
    - name: mynetworks
      value: 172.16.21.10/24
      state: append
    - name: mydestination
      value:
        - example.com
        - example.net
      state: append
    - name: smtpd_use_tls
      value: "yes"          # bool values into qoutation marks
    - name: smtpd_client_restrictions
      value:
        - permit_mynetworks
        - reject_rbl_client sbl.spamhaus.org
        - reject_rbl_client cbl.abuseat.org
        - reject_rbl_client bl.spamcop.net
        - reject_rbl_client b.barracudacentral.org

tasks:

  - name: set postfix params
    postconf:
      name: "{{ item.key }}"
      value: "{{ item.value | string }}"
      state: "{{ item.state | default('present') }}"
    loop: "{{ postfix_main }}"

```

There is important to apply filter `| string` to value. It converts lists
into strings and you don't get warnings from Asnible like this:

*[WARNING]: The value "['permit_mynetworks', 'permit_sasl_authenticated', 'reject_unauth_destination']" (type list) was converted to ""['permit_mynetworks', 'permit_sasl_authenticated',
'reject_unauth_destination']"" (type string). If this does not look like what you expect, quote the entire value to ensure it does not change.*

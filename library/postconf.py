#!/usr/bin/python
# -*- coding: utf-8 -*-

VERSION = "1.0.0"

# Copyright: (c) 2022, Viktor Matys <v.matys@grumpa.net>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: postconf

short_description: Configure Postfix mail server

description: Manage Postfix configuration using postconf command.
             This version manages parameters in main.cf file only.

version_added: "2.10.0"

author:
    - Marius Gedminas (@mgedmin) - inspiration
    - Alexander Galato (@alet) - inspiration 
    - Viktor Matys (@grumpa)

options:
    name:
        description: Name of parameter you want to manage.
        required: true
        type: str
    value:
        description: Value of the parameter. If not set, parameter will have empty value.
        required: false
        type: string
    state:
        description: State of the parameter.
            "present" = add parameter into config file and set the value.
            "absent" = remove the parameter from main.cf (Impossibile to "kill" it from Postfix).
                       If you want to be sure about empty value, use "present" state with empty "value" param.
            For multiple values parameters you may use
            "append" = append this value among the existing values.
                If the parameter doesn't exist, create it (the same as state=present).
            "remove" = remove particular value from others. Non existing value is ignored.
        choices:
            - present
            - absent
            - append
            - remove
        required: false
        default: present
        type: string
'''

EXAMPLES = '''
# Add new parameter
- name: Set mailname parameter to mail.example.com value
  postconf:
    name: mailname
    value: mail.example.com

# Set parameter to empty value (main.cf: "body_checks =")
- name: Set body_checks to empty value
  postconf:
    name: body_checks

# Remove parameter
- name: Remove parameter body_checks from configuration
  postconf:
    name: body_checks
    state: absent

# Append value to multi-value parameter
- name: Add X-our-header to message_drop_headers
  postconf:
    name: message_drop_headers
    value: X-our-header
    state: append
'''

RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule


def run_module():

    module_args = dict(
        name=dict(type='str', required=True),
        value=dict(type='str', required=False, default=''),
        state=dict(type='str', required=False, default='present', choises=["present", "absent", "append", "remove"])
    )

    # default values what module returns
    result = dict(
        changed=False,
        msg='',
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Find commands paths
    postconf_path = module.get_bin_path('postconf', True)
    grep_path = module.get_bin_path('grep', True)

    param_name = module.params.get("name", "")

    # Check if parameter is konwn for Postfix
    rc, std_out, std_err = module.run_command("%s %s %s" % (postconf_path, '-H', param_name))
    if std_err:
        module.fail_json("'%s' is unknown parameter for Postfix." % param_name)

    # Save current value
    rc, std_out, std_err = module.run_command("%s %s %s" % (postconf_path, '-h', param_name))
    if std_err:
        module.fail_json("'%s' is known parameter for Postfix, but returns error." % param_name)
    curr_value = std_out.strip()

    new_value = module.params.get("value", "")
    state = module.params.get("state", "present")

    if state == "present":
        if curr_value != new_value:
            cmd = "%s -e %s='%s'" % (postconf_path, param_name, new_value)
            if not module.check_mode:
                rc, std_out, std_err = module.run_command(cmd)
            result["changed"] = True
            result["msg"] = "Parameter %s was set to '%s'." % (param_name, new_value)
        else:
            result["msg"] = "Parameter %s has already value '%s'." % (param_name, new_value)
    elif state == "absent":
        # Check if parameter exists in main.cf file.
        rc, std_out, std_err = module.run_command("%s ^%s /etc/postfix/main.cf" % (grep_path, param_name))
        if std_out:
            if not module.check_mode:
                rc, std_out, std_err = module.run_command("%s -X %s" % (postconf_path, param_name))
            result["changed"] = True
            result["msg"] = "%s was found in main.cf and was removed." % param_name
        else:
            result["msg"] = "%s wasn't found in main.cf." % param_name
    elif state == "append":
        if curr_value.find(new_value) == -1:
            if not module.check_mode:
                rc, std_out, std_err = module.run_command("%s -e %s='%s %s'" % (postconf_path, param_name, curr_value, new_value))
            result["changed"] = True
            result["msg"] = "%s added to parameter %s (%s)" % (new_value, param_name, curr_value)
        else:
            result["msg"] = "%s already exists in parameter %s (%s)" % (new_value, param_name, curr_value)
    elif state == "remove":
        if curr_value.find(new_value) > -1:
            curr_value = curr_value.replace(new_value, '')
            if not module.check_mode:
                rc, std_out, std_err = module.run_command("%s -e %s='%s'" % (postconf_path, param_name, curr_value))
            result["changed"] = True
            result["msg"] = "%s removed from parameter %s (%s)" % (new_value, param_name, curr_value)
        else:
            result["msg"] = "%s not found parameter %s (%s)" % (new_value, param_name, curr_value)
    else:
        module.fail_json("Unknown state parameter %s" % state)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()

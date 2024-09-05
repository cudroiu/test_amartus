from netmiko import ConnectHandler, NetmikoTimeoutException
import textfsm
import json

OUTPUT_CE1 = """
Interface   Grp  Pri P State   Active          Standby         Virtual IP
Gi0/1         1  150   Active  local           192.168.1.2     192.168.1.253
Gi0/1         2  100   Standby 192.168.1.1     local           192.168.1.254
"""
OUTPUT_CE2 = """
Interface   Grp  Pri P State   Active          Standby         Virtual IP
Gi0/1         1  100   Standby 192.168.1.1     local           192.168.1.253
Gi0/1         2  150   Active  local           192.168.1.2     192.168.1.254
"""
TEMPLATE_PATH = "cisco_ios_show_standby_brief.textfsm"
DEVICE_PAIRS = [
    {
        "CE1": {
            "device_type": "cisco_ios",
            "host": "10.100.15.1",
            "username": "admin",
            "password": "admin"
        },
        "CE2": {
            "device_type": "cisco_ios",
            "host": "10.100.15.2",
            "username": "admin",
            "password": "admin"
        }
    }
]


class HsrpChecker(object):
    def __init__(self, ssh_handler, template, ce_idx, end_result):
        self.ssh_handler = ssh_handler
        self.template = template
        self.ce_idx = ce_idx
        self.end_result = end_result

    def check_hsrp_output(self):
        """
        This method will build the desired json output.
        If the ssh_handler.handler object is valid, run the
        command against the device, otherwise, use the sample
        defined in the constant at the top.
        """
        if self.ssh_handler:
            output = self.ssh_handler.send_command('show standby brief')
        else:
            # if connection is not successful (self.ssh_handler.handler is None), 
            # we will use the constants defined at the top just for the sake of testing.
            if self.ce_idx == 1:
                output = OUTPUT_CE1
            elif self.ce_idx == 2:
                output = OUTPUT_CE2
        with open(self.template) as template:
            fsm = textfsm.TextFSM(template)
            parsed_result = fsm.ParseText(output)
            results = list()
            for item in parsed_result:
                results.append(dict(zip(fsm.header, item)))
            # print(results)
            if self.ce_idx == 1:
                test_result = {
                    'CE1': []
                }
                for item in results:
                    if item['GROUP'] == '1':
                        group1_status = 'Pass' if item['STATE'] == 'Active' else 'Fail - No longer Active'
                        group1_test = {
                            'group': 'Group 1',
                            'status': group1_status
                        }
                        test_result['CE1'].append(group1_test)
                    elif item['GROUP'] == '2':
                        group2_status = 'Pass' if item['STATE'] == 'Standby' else 'Fail - No longer Standby'
                        group2_test = {
                            'group': 'Group 2',
                            'status': group2_status
                        }
                        test_result['CE1'].append(group2_test)
                self.end_result['hsrp_result'].append(test_result)
            elif self.ce_idx == 2:
                test_result = {
                    'CE2': []
                }
                for item in results:
                    if item['GROUP'] == '1':
                        group1_status = 'Pass' if item['STATE'] == 'Standby' else 'Fail - No longer Standby'
                        group1_test = {
                            'group': 'Group 1',
                            'status': group1_status
                        }
                        test_result['CE2'].append(group1_test)
                    elif item['GROUP'] == '2':
                        group2_status = 'Pass' if item['STATE'] == 'Active' else 'Fail - No longer Active'
                        group2_test = {
                            'group': 'Group 2',
                            'status': group2_status
                        }
                        test_result['CE2'].append(group2_test)
                self.end_result['hsrp_result'].append(test_result)


def main():
    for pair in DEVICE_PAIRS:
        hsrp_result = {
            "hsrp_result": []
        }
        # Checking output for CE1
        try:
            with ConnectHandler(**pair['CE1'], timeout=5) as handler_ce1:
                print(f"Successfully connected to CE1 ({pair['CE1']['host']})")
        except NetmikoTimeoutException:
            print(f"Unable to connect to CE1 ({pair['CE1']['host']}). "
                  "We'll use sample output for the sake of demo")
            handler_ce1 = None
        check = HsrpChecker(handler_ce1, template=TEMPLATE_PATH, ce_idx=1, end_result=hsrp_result)
        check.check_hsrp_output()

        # Checking output for CE2
        try:
            with ConnectHandler(**pair['CE2'], timeout=5) as handler_ce2:
                print(f"Successfully connected to CE2 ({pair['CE2']['host']})")
        except NetmikoTimeoutException:
            print(f"Unable to connect to CE2 ({pair['CE2']['host']}). "
                  "We'll use sample output for the sake of demo")
            handler_ce2 = None
        check = HsrpChecker(handler_ce2, template=TEMPLATE_PATH, ce_idx=2, end_result=hsrp_result)
        check.check_hsrp_output()
        print(json.dumps(hsrp_result, indent=4))

if __name__ == '__main__':
    main()
